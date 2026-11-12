# Firmware work required for fixed-wall force measurement

## English

### Goal

Adapt the existing STM32WB55 firmware to measure the force applied by a finger to force sensors mounted on a stationary wall, and deliver usable, calibrated measurements to the desktop application.

This document describes work that remains to be done. It does not assume a particular sensor technology, sensor count, force range, or final data format where those have not yet been specified.

### Current firmware baseline

The project is under [`4_sensors_4_led_working/UART_Example/`](./4_sensors_4_led_working/UART_Example/). It currently:

- Targets the STM32WB55RGV6 and uses STM32CubeWB V1.23.0.
- Configures four 12-bit ADC conversions on channels 1, 2, 5, and 6, corresponding to PC0, PC1, PA0, and PA1.
- Reads the four ADC results sequentially and sends raw values over USB CDC about every 200 ms.
- Formats each line as `C0=<value>  C1=<value>  C2=<value>  C3=<value>`.
- Maps those readings to four PWM outputs, apparently for the original four-LED behavior.
- Does not currently calculate force, tare/zero the sensors, apply calibration, or filter readings.

The 3D macro is only a mechanical concept: its three sensor blocks are placeholders on movable carriages. They do not establish the final sensor count or electrical interface.

### Work to do

#### 1. Confirm the sensor hardware and electrical interface

- Select the actual force sensor(s), their quantity, and their placement on the wall.
- Record each sensor's output type, operating voltage, range, connector, and required signal-conditioning circuit.
- Confirm that every signal connected directly to an STM32 ADC is within the MCU's permitted input-voltage range.
- If the sensors are analog voltage-output devices, verify their output circuit and map them to the selected ADC pins.
- If they are bridge/load-cell sensors, determine the required instrumentation amplifier or external ADC before attempting to use the STM32 ADC directly.
- Confirm whether the final design needs one measurement point or several. The existing firmware has four ADC channels; the 3D concept shows three placeholder positions. Neither determines the final count.

#### 2. Adapt and verify ADC acquisition

- Configure the ADC channels, pins, conversion sequence, and number of sensors to match the confirmed hardware.
- Define the measurement sample rate. The current loop produces approximately five samples per second; confirm whether that is sufficient for the intended finger-force tests.
- Add suitable averaging or digital filtering to reduce noise without hiding meaningful changes in force.
- Detect and report invalid, disconnected, saturated, or out-of-range sensor readings where the hardware allows it.
- Keep raw ADC readings available for diagnostics, even after calibrated force values are introduced.

#### 3. Convert raw readings into force

- Add a zero/tare procedure for the unloaded sensor or wall.
- Calibrate each sensor independently using known reference loads over the intended range.
- Convert readings to an agreed unit, such as newtons (N), and store sensor-specific calibration parameters.
- Use a calibration curve or lookup table if the sensor response is nonlinear; do not assume raw ADC counts are proportional to force.
- Define behavior for readings below zero after tare and for readings above the calibrated range.
- Decide whether tare and calibration are performed only in firmware or can also be requested by the desktop application.

#### 4. Define and implement the USB data protocol

- Replace the current `C0=...` text format or update the desktop parser. The existing parser accepts JSON arrays or whitespace-separated numbers, but does not parse the current labeled format.
- Agree on a line-delimited message schema that identifies sensor readings and their meaning. If sending calibrated force, include the unit and distinguish it from raw ADC counts.
- Decide whether messages also need a sample counter, timestamp, sensor status, or LED status.
- Ensure that the firmware and host agree on the number, order, type, and units of all values. The host currently defaults to four sensors and four LEDs and stores sensor readings as integers; it may need changes for a different count or decimal force values.
- Check the return status from `CDC_Transmit_FS`. It can report `USBD_BUSY`, but the current call site ignores the result; add an appropriate retry, queue, or documented drop policy.
- Implement USB receive-command handling only if host-driven operations such as tare, start/stop, or calibration are required. The current receive callback rearms reception but does not process commands.

#### 5. Revisit the old PWM/LED behavior

- Decide whether the four PWM outputs are still required.
- If retained as indicators, define their behavior independently of force measurement and clamp duty-cycle values to the valid timer range.
- The current PWM calculation uses a 2000-count offset without clamping. Readings below that offset can produce unintended duty-cycle values, so this logic must be corrected before reuse.
- If LEDs are no longer part of the design, remove or disable the unused PWM behavior and update the CubeMX configuration as appropriate.

#### 6. Validate the firmware and end-to-end behavior

- Build the project with the intended STM32CubeIDE/CubeWB setup and resolve any configuration or toolchain issues.
- Verify each ADC channel against the physical sensor connected to it.
- Test zero, known loads, the expected operating range, overload/saturation, and sensor-disconnect behavior.
- Compare firmware output with a USB serial monitor, then verify that the desktop application parses and records the same values and units.
- Check the effective sample rate and whether any USB transmissions are lost under normal operation.
- Keep the sensor pinout, calibration procedure, message schema, and firmware settings documented alongside the project.

### Decisions needed before implementation

1. Exact sensor model/type and analog interface (or amplifier/ADC module).
2. Number of sensors and their mapping to wall positions and MCU pins.
3. Force range, desired unit, and required measurement rate.
4. Whether tare/start/stop/calibration must be controllable from the desktop application.
5. Whether the existing four PWM/LED outputs remain part of the product.

Until these are confirmed, ADC and USB infrastructure can be prepared, but force conversion and final pin/protocol choices should remain provisional.

---

## Português

### Objetivo

Adaptar o firmware existente do STM32WB55 para medir a força aplicada pelo dedo em sensores instalados em uma parede fixa e enviar medições úteis e calibradas para a aplicação desktop.

Este documento descreve o trabalho pendente. Ele não presume uma tecnologia específica de sensor, quantidade de sensores, faixa de força ou formato final dos dados quando essas definições ainda não foram fornecidas.

### Situação atual do firmware

O projeto está em [`4_sensors_4_led_working/UART_Example/`](./4_sensors_4_led_working/UART_Example/). Atualmente, ele:

- Tem como alvo o STM32WB55RGV6 e usa STM32CubeWB V1.23.0.
- Configura quatro conversões ADC de 12 bits nos canais 1, 2, 5 e 6, correspondentes a PC0, PC1, PA0 e PA1.
- Lê os quatro resultados ADC em sequência e envia valores brutos pela USB CDC aproximadamente a cada 200 ms.
- Formata cada linha como `C0=<valor>  C1=<valor>  C2=<valor>  C3=<valor>`.
- Mapeia essas leituras para quatro saídas PWM, aparentemente para o comportamento original de quatro LEDs.
- Ainda não calcula força, não zera os sensores, não aplica calibração e não filtra as leituras.

A macro 3D é apenas um conceito mecânico: seus três blocos de sensor são representações provisórias em carrinhos móveis. Eles não definem a quantidade final de sensores nem sua interface elétrica.

### Trabalho a realizar

#### 1. Confirmar os sensores e a interface elétrica

- Definir o modelo real dos sensores de força, a quantidade e a posição de cada um na parede.
- Registrar o tipo de saída, tensão de operação, faixa de medição, conector e circuito de condicionamento necessário para cada sensor.
- Confirmar que qualquer sinal conectado diretamente ao ADC do STM32 está dentro da faixa de tensão permitida pelo microcontrolador.
- Se os sensores fornecerem uma saída analógica de tensão, validar o circuito de saída e mapeá-los para os pinos ADC escolhidos.
- Se forem sensores em ponte/células de carga, definir o amplificador de instrumentação ou ADC externo necessário antes de tentar usar diretamente o ADC do STM32.
- Confirmar se o projeto final terá um ou vários pontos de medição. O firmware atual tem quatro canais ADC; o conceito 3D mostra três posições provisórias. Nenhum dos dois define a quantidade final.

#### 2. Adaptar e verificar a aquisição ADC

- Configurar canais ADC, pinos, sequência de conversão e quantidade de sensores conforme o hardware confirmado.
- Definir a taxa de amostragem. O loop atual produz aproximadamente cinco amostras por segundo; é preciso confirmar se isso basta para os testes de força pretendidos.
- Adicionar média ou filtragem digital adequada para reduzir ruído sem ocultar mudanças relevantes na força.
- Detectar e indicar leituras inválidas, sensores desconectados, saturação ou valores fora da faixa, quando o hardware permitir.
- Manter as leituras ADC brutas disponíveis para diagnóstico, mesmo depois de adicionar valores de força calibrados.

#### 3. Converter leituras brutas em força

- Adicionar um procedimento de zero/tara com o sensor ou a parede sem carga.
- Calibrar cada sensor individualmente usando cargas de referência conhecidas dentro da faixa pretendida.
- Converter as leituras para uma unidade acordada, como newtons (N), e armazenar parâmetros de calibração específicos de cada sensor.
- Usar uma curva ou tabela de calibração se a resposta do sensor for não linear; não presumir que os valores ADC sejam proporcionais à força.
- Definir o comportamento para leituras abaixo de zero após a tara e para leituras acima da faixa calibrada.
- Decidir se tara e calibração serão executadas somente no firmware ou também poderão ser solicitadas pela aplicação desktop.

#### 4. Definir e implementar o protocolo de dados USB

- Substituir o formato atual `C0=...` ou atualizar o parser desktop. O parser atual aceita arrays JSON ou números separados por espaços, mas não interpreta o formato rotulado enviado pelo firmware.
- Definir um formato de mensagem delimitada por linha que identifique as leituras e o significado de cada valor. Se forem enviadas forças calibradas, incluir a unidade e distingui-las das contagens ADC brutas.
- Decidir se as mensagens também precisam conter contador de amostra, timestamp, estado dos sensores ou estado dos LEDs.
- Garantir que firmware e aplicação concordem com quantidade, ordem, tipo e unidade dos valores. A aplicação atualmente assume quatro sensores e quatro LEDs e armazena as leituras dos sensores como inteiros; poderá precisar de alterações para outra quantidade ou valores decimais de força.
- Verificar o retorno de `CDC_Transmit_FS`. A função pode retornar `USBD_BUSY`, mas o ponto de chamada atual ignora esse resultado; adicionar nova tentativa, fila ou uma política documentada de descarte.
- Implementar o processamento de comandos recebidos por USB somente se forem necessárias operações controladas pela aplicação, como tara, início/fim da medição ou calibração. O callback atual reativa a recepção, mas não processa comandos.

#### 5. Revisar o comportamento antigo de PWM/LEDs

- Decidir se as quatro saídas PWM ainda serão necessárias.
- Se forem mantidas como indicadores, definir seu comportamento independentemente da medição de força e limitar os valores de duty cycle à faixa válida do timer.
- O cálculo PWM atual usa um deslocamento de 2000 contagens sem limitar o resultado. Leituras abaixo desse valor podem produzir duty cycles inesperados; essa lógica precisa ser corrigida antes de ser reutilizada.
- Se os LEDs não fizerem mais parte do projeto, remover ou desativar o comportamento PWM não utilizado e atualizar a configuração do CubeMX conforme necessário.

#### 6. Validar o firmware e o funcionamento ponta a ponta

- Compilar o projeto com a configuração pretendida do STM32CubeIDE/CubeWB e resolver problemas de configuração ou toolchain.
- Verificar cada canal ADC em relação ao sensor físico conectado a ele.
- Testar zero, cargas conhecidas, faixa de operação prevista, sobrecarga/saturação e desconexão do sensor.
- Comparar a saída do firmware em um monitor serial USB e, depois, verificar se a aplicação desktop interpreta e registra os mesmos valores e unidades.
- Conferir a taxa de amostragem efetiva e se há perda de transmissões USB durante o funcionamento normal.
- Manter documentados junto ao projeto o pinout dos sensores, o procedimento de calibração, o formato das mensagens e as configurações do firmware.

### Definições necessárias antes da implementação

1. Modelo/tipo exato do sensor e sua interface analógica (ou módulo amplificador/ADC).
2. Quantidade de sensores e mapeamento para as posições na parede e os pinos do microcontrolador.
3. Faixa de força, unidade desejada e taxa de medição necessária.
4. Se tara/início/fim/calibração devem poder ser controlados pela aplicação desktop.
5. Se as quatro saídas PWM/LED atuais continuarão no produto.

Até essas definições serem confirmadas, é possível preparar a infraestrutura ADC e USB, mas a conversão para força e as escolhas finais de pinos e protocolo devem permanecer provisórias.
