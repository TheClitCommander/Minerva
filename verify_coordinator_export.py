import sys

print("\n=== VERIFYING COORDINATOR EXPORTS ===")
try:
    import web.multi_ai_coordinator
    print("✅ Successfully imported multi_ai_coordinator module")
    
    has_coordinator = False
    if hasattr(web.multi_ai_coordinator, 'Coordinator'):
        print(f"✅ Found Coordinator (capital C): {id(web.multi_ai_coordinator.Coordinator)}")
        has_coordinator = True
    else:
        print("❌ Missing Coordinator (capital C) export")
    
    if hasattr(web.multi_ai_coordinator, 'coordinator'):
        print(f"✅ Found coordinator (lowercase): {id(web.multi_ai_coordinator.coordinator)}")
        has_coordinator = True
    else:
        print("❌ Missing coordinator (lowercase) export")
    
    if not has_coordinator:
        print("❌ No coordinator exports found - this will cause simulated responses")
        sys.exit(1)
    else:
        print("✅ Coordinator exports verified successfully")

except Exception as e:
    print(f"❌ Error importing coordinator: {e}")
    sys.exit(1)
