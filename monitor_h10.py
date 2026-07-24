#!/usr/bin/env python3
"""
Monitor de Frequência Cardíaca — Polar H10
Versão interativa para uso por pessoas leigas.

Dependência: pip install bleak
Build      : build_exe.bat
"""

import asyncio
import csv
import sys
from datetime import datetime
from typing import Optional
from bleak import BleakClient, BleakScanner

HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
INTERVALO_SEGUNDOS = 1

SEP = "-" * 54


# ---------------------------------------------------------------------------
# Helpers de formatação
# ---------------------------------------------------------------------------

def linha(char: str = "-"):
    print(char * 54)

def secao(titulo: str):
    print()
    print(SEP)
    print(f"  {titulo}")
    print(SEP)

def ok(msg: str):
    print(f"  [OK]  {msg}")

def erro(msg: str):
    print(f"  [ERRO]  {msg}")

def info(msg: str):
    print(f"  {msg}")


# ---------------------------------------------------------------------------
# Parsing do pacote GATT Heart Rate Measurement
# ---------------------------------------------------------------------------

def parse_heart_rate(data: bytearray) -> int:
    flags = data[0]
    if flags & 0x01:
        return int.from_bytes(data[1:3], byteorder="little")
    return data[1]


# ---------------------------------------------------------------------------
# Scan BLE
# ---------------------------------------------------------------------------

async def _scan_async(timeout: float = 10.0):
    devices = await BleakScanner.discover(timeout=timeout)
    polar   = [d for d in devices if d.name and "polar" in d.name.lower()]
    outros  = [d for d in devices if d not in polar]
    return polar + outros          # Polar aparece primeiro


# ---------------------------------------------------------------------------
# Perguntas interativas
# ---------------------------------------------------------------------------

def perguntar_endereco() -> str:
    secao("PASSO 1 — Endereco do dispositivo")
    print()
    info("Pressione ENTER para escanear dispositivos Bluetooth proximos.")
    info("Ou digite o endereco do H10 diretamente (ex: A0:B1:C2:D3:E4:F5)")

    while True:
        addr = input("\n  > ").strip()

        # ---- scan automático ----
        if addr == "":
            print()
            info("Escaneando... (aguarde ate 10 segundos)")
            try:
                devices = asyncio.run(_scan_async())
            except Exception as e:
                erro(f"Falha ao escanear: {e}")
                info("Verifique se o Bluetooth esta ativado e tente novamente.")
                continue

            if not devices:
                print()
                erro("Nenhum dispositivo encontrado.")
                info("Verifique se o H10 esta ligado e proximo do computador.")
                info("Pressione ENTER para tentar novamente ou digite o endereco.")
                continue

            print()
            info(f"{len(devices)} dispositivo(s) encontrado(s):\n")
            for i, d in enumerate(devices, 1):
                nome = d.name or "(sem nome)"
                print(f"    {i}.  {nome:<28}  {d.address}")

            print()
            while True:
                escolha = input("  Numero do dispositivo: ").strip()
                if escolha.isdigit():
                    idx = int(escolha) - 1
                    if 0 <= idx < len(devices):
                        return devices[idx].address
                erro("Numero invalido. Tente novamente.")

        # ---- endereço manual ----
        addr = addr.upper()
        partes = addr.split(":")
        if len(partes) == 6 and all(len(p) == 2 for p in partes):
            return addr
        erro("Formato invalido. Use XX:XX:XX:XX:XX:XX  (ex: A0:B1:C2:D3:E4:F5)")


def perguntar_duracao() -> Optional[int]:
    secao("PASSO 2 — Duracao do teste")
    print()
    info("Digite o tempo em minutos  (exemplos: 10  ou  5.5  para 5min 30s)")
    info("Ou pressione ENTER para rodar sem limite  (Ctrl+C para parar)")

    while True:
        val = input("\n  > ").strip().replace(",", ".")
        if val == "":
            return None
        try:
            minutos = float(val)
            if minutos <= 0:
                erro("O tempo deve ser maior que zero.")
                continue
            return int(minutos * 60)
        except ValueError:
            erro("Valor invalido. Digite um numero, por exemplo: 10")


# ---------------------------------------------------------------------------
# Monitor de FC
# ---------------------------------------------------------------------------

class HeartRateMonitor:
    def __init__(self, address: str, output_file: str, duration: Optional[int]):
        self.address     = address
        self.output_file = output_file
        self.duration    = duration

        self.last_hr: Optional[int] = None
        self._stop   = asyncio.Event()
        self._count  = 0
        self._start_ts: Optional[datetime] = None
        self._connected = False

    def stop(self):
        self._stop.set()

    def _on_hr_notification(self, sender, data: bytearray):
        self.last_hr = parse_heart_rate(data)

    async def _log_loop(self, writer: csv.writer, file_handle):
        elapsed = 0
        self._start_ts = datetime.now()

        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=INTERVALO_SEGUNDOS)
                break
            except asyncio.TimeoutError:
                pass

            elapsed      += INTERVALO_SEGUNDOS
            self._count  += 1
            now = datetime.now()
            hr  = self.last_hr

            if hr is not None:
                writer.writerow([now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), hr])
                file_handle.flush()
                print(f"  [{now.strftime('%H:%M:%S')}]   {hr:3d} bpm   (leitura #{self._count})")
            else:
                print(f"  [{now.strftime('%H:%M:%S')}]   --- sem sinal de FC   (#{self._count})")

            if self.duration is not None and elapsed >= self.duration:
                self._stop.set()

    async def run(self) -> bool:
        secao("CONECTANDO")
        print()
        info(f"Conectando a {self.address} ...")

        try:
            async with BleakClient(self.address, timeout=15.0) as client:
                if not client.is_connected:
                    erro("Nao foi possivel conectar ao dispositivo.")
                    info("Verifique se o H10 esta ligado e proximo.")
                    return False

                self._connected = True
                ok("Conectado com sucesso!")

                secao("TESTE EM ANDAMENTO")
                print()
                if self.duration:
                    m, s = divmod(self.duration, 60)
                    info(f"Duracao   : {m}m {s}s  ({self.duration}s no total)")
                else:
                    info("Duracao   : sem limite  (Ctrl+C para parar)")
                info(f"Intervalo : {INTERVALO_SEGUNDOS} segundos")
                info(f"Arquivo   : {self.output_file}")
                print()

                with open(self.output_file, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(["data", "hora", "bpm"])
                    fh.flush()

                    await client.start_notify(
                        HEART_RATE_MEASUREMENT_UUID, self._on_hr_notification
                    )
                    try:
                        await self._log_loop(writer, fh)
                    finally:
                        await client.stop_notify(HEART_RATE_MEASUREMENT_UUID)

        except OSError as exc:
            erro(f"Falha de conexao Bluetooth: {exc}")
            info("Verifique se o H10 esta ligado, proximo e emparelhado.")
            return False
        except Exception as exc:
            erro(f"Erro inesperado: {exc}")
            return False

        return True

    def imprimir_resumo(self):
        secao("RESUMO DO TESTE")
        print()
        if self._start_ts and self._count > 0:
            fim     = datetime.now()
            total_s = int((fim - self._start_ts).total_seconds())
            m, s    = divmod(total_s, 60)
            info(f"Inicio    : {self._start_ts.strftime('%d/%m/%Y %H:%M:%S')}")
            info(f"Fim       : {fim.strftime('%d/%m/%Y %H:%M:%S')}")
            info(f"Duracao   : {m}m {s}s")
            info(f"Leituras  : {self._count}")
            info(f"Arquivo   : {self.output_file}")
        elif not self._connected:
            info("Nenhum dado coletado — conexao nao estabelecida.")
        else:
            info("Nenhuma leitura registrada.")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def cabecalho():
    print()
    print("=" * 54)
    print("    MONITOR DE FREQUENCIA CARDIACA — POLAR H10")
    print("=" * 54)


def main():
    cabecalho()

    try:
        address  = perguntar_endereco()
        duration = perguntar_duracao()
    except KeyboardInterrupt:
        print("\n\n  Cancelado pelo usuario.")
        input("\n  Pressione ENTER para fechar...")
        return

    output  = f"hr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    monitor = HeartRateMonitor(address, output, duration)

    sucesso = False
    try:
        sucesso = asyncio.run(monitor.run())
    except KeyboardInterrupt:
        monitor.stop()
        print("\n\n  Interrompido pelo usuario.")

    monitor.imprimir_resumo()

    if sucesso and monitor._count > 0:
        print(f"  Arquivo salvo: {output}")
    elif not sucesso:
        print("  Nenhum arquivo gerado devido a falha na conexao.")

    input("\n  Pressione ENTER para fechar...")


if __name__ == "__main__":
    main()
