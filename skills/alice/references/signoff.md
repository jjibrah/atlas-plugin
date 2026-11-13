# Client sign-off

The user says the client approved the proposal or the PRD. `atlas begin alice --stage none` has run.

1. Ask, in one question, for whatever is missing: **who** approved (name or role) and **how** (email of 12 Nov, signed PDF, said in the meeting), and which version they saw. Never invent either.
2. In the PRD: set the Status row to `Approved by client`, raise the version and add a changelog row ("Approved by <role>"). Leave the proposal as the client saw it.
3. `alice.py check P` must pass. Fix what fails first.
4. Record it, naming the versions the client saw (this also snapshots both documents):
   ```
   atlas signoff --what "Proposal v0.2 / PRD v0.4" --by "<client person or role>" --evidence "<how>"
   ```
5. `atlas finish alice --stage none` logs the new version and runs gate G1. If it prints "To pass G1", relay the items (usually an open "needed before we start" question). Otherwise Stark is next.
