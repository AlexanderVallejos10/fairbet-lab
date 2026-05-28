# Lecciones aprendidas

## 1. Estructura
Al principio se intentó separar demasiado el proyecto. Eso hizo que los imports se volvieran confusos. Se corrigió usando una estructura más clara.

## 2. Wallet
La wallet no debía guardar saldo fijo. Al calcularlo desde movimientos fue más fácil evitar errores.

## 3. Concurrencia
Sin bloqueo de cuentas podían entrar dos operaciones al mismo tiempo. Se corrigió con transacciones y `select_for_update`.

## 4. Autoexclusión
Primero se pensó solo como una tabla aparte. Luego se vio que también debía reflejarse en el perfil del usuario para bloquear apuestas.

## 5. Tests
Los tests ayudaron a revisar si la lógica principal sí estaba funcionando. Sin ellos era fácil romper algo sin notarlo.

## 6. Cierre
La mejor decisión fue mantener todo simple y explicable.