# Boceto ER del wallet

Dibujar a mano:
- User
- UserProfile
- WalletAccount
- LedgerTransaction
- LedgerEntry
- IdempotencyKey

Relacionar:
- User -> UserProfile
- User -> WalletAccount
- WalletAccount -> LedgerEntry
- LedgerTransaction -> LedgerEntry
- LedgerTransaction -> IdempotencyKey