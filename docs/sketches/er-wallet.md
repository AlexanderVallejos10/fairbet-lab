# Boceto: ER del wallet

Dibujar:
- User
- UserProfile
- WalletAccount
- LedgerTransaction
- LedgerEntry
- IdempotencyKey

Poner flechas entre:
- User -> UserProfile
- User -> WalletAccount
- WalletAccount -> LedgerEntry
- LedgerTransaction -> LedgerEntry
- LedgerTransaction -> IdempotencyKey