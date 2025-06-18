# ⚖️ Minerva Ephemeral Rules (Active Working Guidelines)

These are the non-negotiable standards and expectations during the Minerva rebuild.

## 🧠 **1. No Fallback Logic**
- Do **not** simulate working behavior.
- No placeholder messages like "connected" if the system isn't actually connected.
- If something fails, **show real errors**, not mock responses or backups.

> ❌ Fake loading → ✅ Honest failure with retry logic  
> ❌ Simulated chat → ✅ Real API or clear offline message  

## 🧱 **2. Build on Working Solutions**
- Don't start over unless absolutely necessary.
- Use what was already working and build outward.
- Never regress to a less functional version just because it's cleaner on paper.

## 💡 **3. Every Feature Must Actually Work**
- Clicking a button **must** do something.
- If a feature is displayed in the UI, **it must be functional**, or removed.
- Orb menu? It better trigger scene switches.  
- Chat box? It better send real messages or explain why it can't.

## 📋 **4. Visual Progress Must Match Functional Progress**
- If the UI changes visually, it **must reflect real code underneath**.
- No illusion of interactivity without real functionality behind it.
- No "finished" screens if the backend doesn't support it.

## 🔥 **5. No More Backup Responses**
- Cascade is **not allowed to say "just in case it fails"** or "here's a temporary screen."
- All implementations are **final, real, and locked-in**.

## 🛠️ **6. Fix > Fake**
- All energy should be spent fixing actual bugs, not masking them.
- No defensive code that hides real issues.
- Crashes are better than fakes — we can fix crashes.

## 🌀 **7. The Orb Is Sacred**
- The Minerva Orb must:
  - Open a real radial menu
  - Trigger functional scene transitions
  - Center the entire navigation experience
- If the Orb is present, it must do what it promises. Always.

## 🧭 **8. Cursor AI Is the New Dev Interface**
- All instructions, code generation, and updates should assume you're using **Cursor AI**
- This means:
  - File-specific changes
  - Modular component updates
  - Live system sync, no manual guesswork

## 🔓 **9. Unlock True Functionality**
- Minerva is not a UI showcase — it's a **control center**, a **dashboard**, a **live system**.
- That means:
  - The Memory tab pulls live memory
  - The Projects panel shows actual project data
  - The Chat talks to real LLMs (or clearly explains why it can't)

## 🤬 **10. No Bullshit**
- No fake confirmations.
- No pretending something works when it doesn't.
- No vague statements like "should be fine" or "you can probably."
- Either it works, or we fix it until it does. 