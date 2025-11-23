"""
Business logic for SplitJourney.
Handles group management and expense calculations.
"""
from sqlalchemy.orm import Session
from core.models import Group, User, GroupMember, Expense, ExpenseSplit
from datetime import datetime

def create_group(db: Session, name: str, creator: User, member_names: list[str]) -> Group:
    """
    Creates a new group and adds members.
    'member_names' is a list of strings.
    The creator is automatically added as a member (linked to their User account).
    Other members are added as GroupMember entries (initially without User links, unless we match emails later).
    """
    group = Group(name=name, created_by_user_id=creator.id)
    db.add(group)
    db.flush() # Get ID
    
    # Add creator as a member
    creator_member = GroupMember(group_id=group.id, member_name=creator.name, user_id=creator.id)
    db.add(creator_member)
    
    # Add other members
    for m_name in member_names:
        m_name = m_name.strip()
        if m_name:
            # Check if we already added this name (simple dedup)
            if m_name != creator.name: 
                member = GroupMember(group_id=group.id, member_name=m_name)
                db.add(member)
            
    db.commit()
    db.refresh(group)
    return group

def get_groups_for_user(db: Session, user: User):
    """
    Returns all groups where the user is a member.
    """
    # Query GroupMembers linked to this user_id
    memberships = db.query(GroupMember).filter(GroupMember.user_id == user.id).all()
    # Return the associated groups
    return [m.group for m in memberships]

def get_group_details(db: Session, group_id: int) -> Group | None:
    """
    Returns the group with the given ID.
    """
    return db.query(Group).filter(Group.id == group_id).first()

def create_expense(
    db: Session, 
    group_id: int, 
    payer_member_id: int, 
    description: str, 
    amount: float,
    date: datetime,
    split_type: str,
    split_inputs: dict
) -> Expense:
    """
    Creates an expense and splits it according to the split_type.
    split_inputs: dict mapping member_id (int) -> value (amount, percentage, or shares)
    """
    expense = Expense(
        description=description,
        amount=amount,
        group_id=group_id,
        payer_member_id=payer_member_id,
        date=date
    )
    db.add(expense)
    db.flush()
    
    group = db.query(Group).filter(Group.id == group_id).first()
    members = group.members
    
    splits = []
    
    if split_type == "Equal":
        # For Equal split, split_inputs contains {member_id: True/False} for selected members
        # Filter to only selected members
        selected_members = []
        if split_inputs:
            # If split_inputs provided, use only selected members
            for member in members:
                if split_inputs.get(member.id, False):
                    selected_members.append(member)
        else:
            # If no split_inputs (backward compatibility), include all
            selected_members = members
            
        num_selected = len(selected_members)
        if num_selected > 0:
            split_amount = amount / num_selected
            for member in selected_members:
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    member_id=member.id,
                    amount_owed=split_amount
                ))
                
    elif split_type == "Unequal":
        # split_inputs: {member_id: amount}
        total_split = 0
        for member in members:
            owed = float(split_inputs.get(member.id, 0))
            splits.append(ExpenseSplit(
                expense_id=expense.id,
                member_id=member.id,
                amount_owed=owed
            ))
            total_split += owed
            
        # Validation could happen here or in UI, but let's ensure we don't drift too much
        # For now, trust the UI passed valid data or close enough
        
    elif split_type == "Percentage":
        # split_inputs: {member_id: percentage}
        for member in members:
            pct = float(split_inputs.get(member.id, 0))
            owed = (pct / 100.0) * amount
            splits.append(ExpenseSplit(
                expense_id=expense.id,
                member_id=member.id,
                amount_owed=owed
            ))
            
    elif split_type == "Shares":
        # split_inputs: {member_id: shares}
        total_shares = sum(float(val) for val in split_inputs.values())
        if total_shares > 0:
            cost_per_share = amount / total_shares
            for member in members:
                shares = float(split_inputs.get(member.id, 0))
                owed = shares * cost_per_share
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    member_id=member.id,
                    amount_owed=owed
                ))
    
    db.add_all(splits)
    db.commit()
    db.refresh(expense)
    return expense

def calculate_member_balances(db: Session, group_id: int) -> dict[int, float]:
    """
    Calculates net balance for each member in the group.
    Returns dict: {member_id: net_amount}
    Positive = should receive, Negative = should pay.
    """
    from core.models import Settlement
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return {}
        
    balances = {m.id: 0.0 for m in group.members}
    
    # 1. Add amounts paid (Creditor)
    expenses = db.query(Expense).filter(Expense.group_id == group_id).all()
    for exp in expenses:
        if exp.payer_member_id in balances:
            balances[exp.payer_member_id] += exp.amount
            
    # 2. Subtract amounts owed (Debtor)
    for exp in expenses:
        for split in exp.splits:
            if split.member_id in balances:
                balances[split.member_id] -= split.amount_owed
    
    # 3. Account for settlements
    settlements = db.query(Settlement).filter(Settlement.group_id == group_id).all()
    for settlement in settlements:
        # Payer gave money, so their debt decreases (balance increases)
        if settlement.payer_member_id in balances:
            balances[settlement.payer_member_id] += settlement.amount
        # Receiver got money, so what they're owed decreases (balance decreases)
        if settlement.receiver_member_id in balances:
            balances[settlement.receiver_member_id] -= settlement.amount
                
    return balances

def simplify_debts(balances: dict[int, float]) -> list[tuple[int, int, float]]:
    """
    Simplifies debts using a greedy algorithm.
    Returns list of (payer_id, receiver_id, amount).
    """
    debtors = []
    creditors = []
    
    for m_id, amount in balances.items():
        # Round to avoid float precision issues
        amount = round(amount, 2)
        if amount < -0.01:
            debtors.append({'id': m_id, 'amount': amount})
        elif amount > 0.01:
            creditors.append({'id': m_id, 'amount': amount})
            
    # Sort by magnitude (optional, but can help stability)
    debtors.sort(key=lambda x: x['amount'])
    creditors.sort(key=lambda x: x['amount'], reverse=True)
    
    transactions = []
    
    i = 0 # debtor index
    j = 0 # creditor index
    
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        # Amount to settle is min of what debtor owes and creditor is owed
        amount = min(abs(debtor['amount']), creditor['amount'])
        
        transactions.append((debtor['id'], creditor['id'], amount))
        
        # Update remaining amounts
        debtor['amount'] += amount
        creditor['amount'] -= amount
        
        # Move indices if settled (approx zero)
        if abs(debtor['amount']) < 0.01:
            i += 1
        if creditor['amount'] < 0.01:
            j += 1
            
    return transactions

def update_expense(
    db: Session,
    expense_id: int,
    description: str,
    amount: float,
    payer_member_id: int,
    split_type: str,
    split_inputs: dict
) -> Expense:
    """
    Updates an existing expense and its splits.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise ValueError("Expense not found")
    
    # Update basic expense fields
    expense.description = description
    expense.amount = amount
    expense.payer_member_id = payer_member_id
    
    # Delete old splits
    db.query(ExpenseSplit).filter(ExpenseSplit.expense_id == expense_id).delete()
    
    # Create new splits using the same logic as create_expense
    group = db.query(Group).filter(Group.id == expense.group_id).first()
    members = group.members
    
    splits = []
    
    if split_type == "Equal":
        selected_members = []
        if split_inputs:
            for member in members:
                if split_inputs.get(member.id, False):
                    selected_members.append(member)
        else:
            selected_members = members
            
        num_selected = len(selected_members)
        if num_selected > 0:
            split_amount = amount / num_selected
            for member in selected_members:
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    member_id=member.id,
                    amount_owed=split_amount
                ))
                
    elif split_type == "Unequal":
        for member in members:
            owed = float(split_inputs.get(member.id, 0))
            splits.append(ExpenseSplit(
                expense_id=expense.id,
                member_id=member.id,
                amount_owed=owed
            ))
            
    elif split_type == "Percentage":
        for member in members:
            pct = float(split_inputs.get(member.id, 0))
            owed = (pct / 100.0) * amount
            splits.append(ExpenseSplit(
                expense_id=expense.id,
                member_id=member.id,
                amount_owed=owed
            ))
            
    elif split_type == "Shares":
        total_shares = sum(float(val) for val in split_inputs.values())
        if total_shares > 0:
            cost_per_share = amount / total_shares
            for member in members:
                shares = float(split_inputs.get(member.id, 0))
                owed = shares * cost_per_share
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    member_id=member.id,
                    amount_owed=owed
                ))
    
    db.add_all(splits)
    db.commit()
    db.refresh(expense)
    return expense

def delete_expense(db: Session, expense_id: int):
    """
    Deletes an expense and all its splits.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense:
        db.delete(expense)
        db.commit()

def record_settlement(db: Session, group_id: int, payer_member_id: int, receiver_member_id: int, amount: float):
    """
    Records a payment/settlement between two members.
    """
    from core.models import Settlement
    
    settlement = Settlement(
        group_id=group_id,
        payer_member_id=payer_member_id,
        receiver_member_id=receiver_member_id,
        amount=amount,
        date=datetime.utcnow()
    )
    db.add(settlement)
    db.commit()
    return settlement

# ==================== CHAT FUNCTIONS ====================

def add_message(db: Session, group_id: int, sender_member_id: int, text: str):
    """
    Adds a new chat message to a group.
    
    Args:
        db: Database session
        group_id: ID of the group
        sender_member_id: ID of the member sending the message
        text: Message content
        
    Returns:
        Message: The created message object
    """
    from core.models import Message
    
    message = Message(
        group_id=group_id,
        sender_member_id=sender_member_id,
        text=text,
        created_at=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_messages(db: Session, group_id: int):
    """
    Retrieves all chat messages for a group, ordered chronologically.
    
    Args:
        db: Database session
        group_id: ID of the group
        
    Returns:
        List[Message]: Messages ordered by created_at ascending
    """
    from core.models import Message
    
    messages = db.query(Message).filter(
        Message.group_id == group_id
    ).order_by(Message.created_at.asc()).all()
    
    return messages

# ==================== POLL FUNCTIONS ====================

def create_poll(db: Session, group_id: int, question: str, options: list, creator_member_id: int):
    """
    Creates a new poll in a group.
    
    Args:
        db: Database session
        group_id: ID of the group
        question: Poll question
        options: List of option texts (strings)
        creator_member_id: ID of the member creating the poll
        
    Returns:
        Poll: The created poll object with options
    """
    from core.models import Poll, PollOption
    
    poll = Poll(
        group_id=group_id,
        question=question,
        created_by_member_id=creator_member_id,
        created_at=datetime.utcnow()
    )
    db.add(poll)
    db.flush()  # Get poll.id before adding options
    
    # Create poll options
    for option_text in options:
        if option_text.strip():  # Only add non-empty options
            poll_option = PollOption(
                poll_id=poll.id,
                text=option_text.strip()
            )
            db.add(poll_option)
    
    db.commit()
    db.refresh(poll)
    return poll

def get_polls(db: Session, group_id: int):
    """
    Retrieves all polls for a group, ordered by creation date descending.
    
    Args:
        db: Database session
        group_id: ID of the group
        
    Returns:
        List[Poll]: Polls ordered by created_at descending
    """
    from core.models import Poll
    
    polls = db.query(Poll).filter(
        Poll.group_id == group_id
    ).order_by(Poll.created_at.desc()).all()
    
    return polls

def vote_poll(db: Session, poll_id: int, option_id: int, member_id: int):
    """
    Records a vote on a poll option.
    Ensures one vote per member per poll (will update existing vote).
    
    Args:
        db: Database session
        poll_id: ID of the poll
        option_id: ID of the option being voted for
        member_id: ID of the voting member
        
    Returns:
        PollVote: The vote record
        
    Raises:
        ValueError: If poll or option doesn't exist
    """
    from core.models import PollVote, Poll, PollOption
    
    # Verify poll and option exist
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise ValueError("Poll not found")
        
    option = db.query(PollOption).filter(
        PollOption.id == option_id,
        PollOption.poll_id == poll_id
    ).first()
    if not option:
        raise ValueError("Option not found for this poll")
    
    # Check if member already voted
    existing_vote = db.query(PollVote).filter(
        PollVote.poll_id == poll_id,
        PollVote.member_id == member_id
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.option_id = option_id
        existing_vote.created_at = datetime.utcnow()
        vote = existing_vote
    else:
        # Create new vote
        vote = PollVote(
            poll_id=poll_id,
            option_id=option_id,
            member_id=member_id,
            created_at=datetime.utcnow()
        )
        db.add(vote)
    
    db.commit()
    db.refresh(vote)
    return vote

def get_poll_results(db: Session, poll_id: int):
    """
    Calculates poll results with vote counts and percentages.
    
    Args:
        db: Database session
        poll_id: ID of the poll
        
    Returns:
        dict: {
            'total_votes': int,
            'options': [
                {
                    'id': int,
                    'text': str,
                    'votes': int,
                    'percentage': float
                },
                ...
            ]
        }
    """
    from core.models import Poll, PollOption, PollVote
    
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        return {'total_votes': 0, 'options': []}
    
    # Get all votes for this poll
    votes = db.query(PollVote).filter(PollVote.poll_id == poll_id).all()
    total_votes = len(votes)
    
    # Count votes per option
    vote_counts = {}
    for vote in votes:
        vote_counts[vote.option_id] = vote_counts.get(vote.option_id, 0) + 1
    
    # Build results
    results = []
    for option in poll.options:
        vote_count = vote_counts.get(option.id, 0)
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        
        results.append({
            'id': option.id,
            'text': option.text,
            'votes': vote_count,
            'percentage': percentage
        })
    
    return {
        'total_votes': total_votes,
        'options': results
    }

def get_member_vote(db: Session, poll_id: int, member_id: int):
    """
    Gets the member's vote for a specific poll, if any.
    
    Args:
        db: Database session
        poll_id: ID of the poll
        member_id: ID of the member
        
    Returns:
        PollVote or None: The member's vote if exists
    """
    from core.models import PollVote
    
    vote = db.query(PollVote).filter(
        PollVote.poll_id == poll_id,
        PollVote.member_id == member_id
    ).first()
    
    return vote

# ==================== BUDGET FUNCTIONS ====================

def update_group_budget(db: Session, group_id: int, budget_amount: float):
    """
    Sets or updates the budget for a group.
    
    Args:
        db: Database session
        group_id: ID of the group
        budget_amount: Budget amount (None to remove budget)
        
    Returns:
        Group: Updated group object
    """
    from core.models import Group
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise ValueError("Group not found")
    
    group.budget_amount = budget_amount if budget_amount and budget_amount > 0 else None
    db.commit()
    db.refresh(group)
    return group

def calculate_total_spent(db: Session, group_id: int) -> float:
    """
    Calculates the total amount spent in a group.
    
    Args:
        db: Database session
        group_id: ID of the group
        
    Returns:
        float: Total of all expenses in the group
    """
    from core.models import Expense
    
    expenses = db.query(Expense).filter(Expense.group_id == group_id).all()
    total = sum(expense.amount for expense in expenses)
    return total

def get_budget_status(db: Session, group_id: int) -> dict:
    """
    Gets the budget status with alerts for a group.
    
    Args:
        db: Database session
        group_id: ID of the group
        
    Returns:
        dict: {
            'total_spent': float,
            'budget_amount': float | None,
            'percentage_used': float,
            'alerts': list[str]
        }
    """
    from core.models import Group
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return {
            'total_spent': 0,
            'budget_amount': None,
            'percentage_used': 0,
            'alerts': []
        }
    
    total_spent = calculate_total_spent(db, group_id)
    budget_amount = group.budget_amount
    percentage_used = 0
    alerts = []
    
    if budget_amount and budget_amount > 0:
        percentage_used = (total_spent / budget_amount) * 100
        
        # Generate alerts based on percentage
        if percentage_used >= 100:
            overage = percentage_used - 100
            alerts.append(f"❗ Budget exceeded by {overage:.1f}%")
        elif percentage_used >= 80:
            alerts.append("⚠ 80% of budget used - nearing limit")
        elif percentage_used >= 50:
            alerts.append("⚠ 50% of budget used")
    
    return {
        'total_spent': total_spent,
        'budget_amount': budget_amount,
        'percentage_used': percentage_used,
        'alerts': alerts
    }

# ==================== PLACE TAGGING FUNCTIONS ====================

def tag_place_to_expense(db: Session, expense_id: int, place_data: dict):
    """
    Tags a Google Place to an expense.
    
    Args:
        db: Database session
        expense_id: ID of the expense to tag
        place_data: Dictionary with keys:
            - place_id: Google place ID
            - name: Place name
            - address: Full address
            - latitude: Latitude coordinate
            - longitude: Longitude coordinate
            
    Returns:
        PlaceTag: The created or updated place tag
    """
    from core.models import PlaceTag, Expense
    
    # Check if expense exists
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise ValueError("Expense not found")
    
    # Check if place tag already exists
    existing_tag = db.query(PlaceTag).filter(PlaceTag.expense_id == expense_id).first()
    
    if existing_tag:
        # Update existing tag
        existing_tag.place_id = place_data['place_id']
        existing_tag.name = place_data['name']
        existing_tag.address = place_data.get('address')
        existing_tag.latitude = place_data.get('latitude')
        existing_tag.longitude = place_data.get('longitude')
        db.commit()
        db.refresh(existing_tag)
        return existing_tag
    else:
        # Create new tag
        place_tag = PlaceTag(
            expense_id=expense_id,
            place_id=place_data['place_id'],
            name=place_data['name'],
            address=place_data.get('address'),
            latitude=place_data.get('latitude'),
            longitude=place_data.get('longitude')
        )
        db.add(place_tag)
        db.commit()
        db.refresh(place_tag)
        return place_tag

def get_expense_place(db: Session, expense_id: int):
    """
    Gets the tagged place for an expense.
    
    Args:
        db: Database session
        expense_id: ID of the expense
        
    Returns:
        PlaceTag object if exists, None otherwise
    """
    from core.models import PlaceTag
    
    return db.query(PlaceTag).filter(PlaceTag.expense_id == expense_id).first()

def remove_place_tag(db: Session, expense_id: int):
    """
    Removes place tag from an expense.
    
    Args:
        db: Database session
        expense_id: ID of the expense
        
    Returns:
        bool: True if tag was removed, False if no tag existed
    """
    from core.models import PlaceTag
    
    place_tag = db.query(PlaceTag).filter(PlaceTag.expense_id == expense_id).first()
    if place_tag:
        db.delete(place_tag)
        db.commit()
        return True
    return False
