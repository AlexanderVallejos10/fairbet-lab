# Lecciones aprendidas

## 1. Estructura
Al principio el proyecto quedó más complejo de lo necesario.  
Se corrigió volviendo a una estructura más simple.

## 2. Wallet
El saldo no se guarda.  
Se calcula desde movimientos para evitar errores.

## 3. Concurrencia
Sin bloqueo de cuentas podían entrar dos operaciones al mismo tiempo.  
Se corrigió con transacciones.

## 4. Autoexclusión
Primero quedó solo en una tabla aparte.  
Luego se reflejó también en el perfil del usuario.

## 5. Tests
Los tests ayudaron a revisar si la lógica principal sí estaba funcionando.

## 6. Cierre
La mejor decisión fue mantener todo simple y explicable.