"""
Test script for SplitJourney.
Verifies the core flow: Signup -> Create Group -> Add Expense -> Check Balances.
"""
import os
from core.db import init_db, SessionLocal, engine, Base
from core.auth import create_user, authenticate_user
from core.logic import create_group, create_expense, calculate_member_balances, simplify_debts
from datetime import datetime

def test_flow():
    print("--- Starting Test Flow ---")
    
    # 1. Initialize DB (ensure tables exist)
    init_db()
    db = SessionLocal()
    
    # Clean up previous test data if needed (optional, or just use unique names)
    # For this test, we'll just create unique users based on timestamp
    ts = int(datetime.utcnow().timestamp())
    email_alice = f"alice_{ts}@example.com"
    email_bob = f"bob_{ts}@example.com"
    
    print(f"1. Creating Users: {email_alice}, {email_bob}")
    user_alice = create_user(db, "Alice", email_alice, "password123")
    user_bob = create_user(db, "Bob", email_bob, "password123")
    
    assert user_alice is not None, "Failed to create Alice"
    assert user_bob is not None, "Failed to create Bob"
    print("   -> Users created successfully.")
    
    # 2. Authenticate
    print("2. Authenticating Alice...")
    logged_in_alice = authenticate_user(db, email_alice, "password123")
    assert logged_in_alice is not None, "Authentication failed"
    assert logged_in_alice.id == user_alice.id
    print("   -> Authentication successful.")
    
    # 3. Create Group
    print("3. Creating Group 'Trip' with Alice and Bob...")
    # Alice creates group, adds Bob
    group = create_group(db, "Trip", user_alice, ["Bob"])
    print(f"   -> Group created with ID {group.id}")
    
    # Verify members
    # Alice should be linked to her User, Bob is just a name for now (unless we link him)
    # In our logic `create_group` adds members by name. 
    # If we want to link Bob-the-User to Bob-the-Member, we'd need extra logic, 
    # but for now let's just verify the members exist.
    members = group.members
    print(f"   -> Members: {[m.member_name for m in members]}")
    assert len(members) == 2
    
    # Find member IDs
    alice_member = next(m for m in members if m.member_name == "Alice")
    bob_member = next(m for m in members if m.member_name == "Bob")
    
    # 4. Add Expense
    print("4. Adding Expense: Lunch Rs. 200 paid by Alice (Equal Split)...")
    # Split equally: 100 each
    split_inputs = {} # Not needed for Equal
    
    create_expense(
        db,
        group.id,
        alice_member.id,
        "Lunch",
        200.0,
        datetime.utcnow(),
        "Equal",
        split_inputs
    )
    print("   -> Expense added.")
    
    # 5. Check Balances
    print("5. Calculating Balances...")
    balances = calculate_member_balances(db, group.id)
    
    # Alice paid 200. Her share is 100. She should receive 100.
    # Bob paid 0. His share is 100. He should pay 100.
    
    print(f"   -> Alice Balance: {balances[alice_member.id]}")
    print(f"   -> Bob Balance: {balances[bob_member.id]}")
    
    assert balances[alice_member.id] == 100.0
    assert balances[bob_member.id] == -100.0
    print("   -> Balances correct.")
    
    # 6. Simplify Debts
    print("6. Simplifying Debts...")
    transactions = simplify_debts(balances)
    for payer, receiver, amount in transactions:
        print(f"   -> Transaction: Member {payer} pays Member {receiver} Rs. {amount}")
        
    assert len(transactions) == 1
    assert transactions[0][0] == bob_member.id # Payer
    assert transactions[0][1] == alice_member.id # Receiver
    assert transactions[0][2] == 100.0
    print("   -> Debt simplification correct.")
    
    db.close()
    print("--- Test Passed Successfully ---")

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print(f"\n!!! TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
