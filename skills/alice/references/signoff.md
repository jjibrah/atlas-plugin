# Client sign-off

The user says the client approved the proposal or the PRD. `atlas begin alice --stage none` has run.

1. Ask, in one question, for whatever is missing: **who** approved (name or role) and **how** (email of 12 Nov, signed PDF, said in the meeting), and which version they saw. Never invent either.
2. `atlas scope`. If it lists differences from the proposal that was sent, the client approved the version they saw, not these: settle them first (`references/scope.md` §2). Recording the sign-off makes the PRD as it stands "what was agreed".
3. In the PRD: set the Status row to `Approved by client`, raise the version and add a changelog row ("Approved by <role>"). Leave the proposal as the client saw it.
4. `alice.py check P` must pass. Fix what fails first.
5. Record it, naming the versions the client saw (this also snapshots both documents and freezes the agreed requirements):
   ```
   atlas signoff --what "Proposal v0.2 / PRD v0.4" --by "<client person or role>" --evidence "<how>"
   ```
6. `atlas finish alice --stage none` logs the new version and runs gate G1. If it prints "To pass G1", relay the items in plain words (usually a question the client must answer before we start).
7. **Offer the next step, in plain words:** "The client approved. I can prepare the diagram pack (how the system will work, as pictures you can show them). Shall I?" On yes: load the stark skill and follow its `diagrams` mode now, in this session. On no: say that the design is next whenever they are ready.
