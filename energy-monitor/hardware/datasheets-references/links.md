# Datasheet and reference links

Official sources only. No datasheet PDFs are copied into this repository: they are
third-party documents whose redistribution terms vary, and a link stays current
while a copy ages.

| Ref | Document | Link | Used for |
|---|---|---|---|
| `ti-ina226` | Texas Instruments INA226 — 36 V, 16-bit I²C current/voltage/power monitor | https://www.ti.com/product/INA226 · https://www.ti.com/lit/ds/symlink/ina226.pdf | LSBs, full-scale ranges, supply range, address straps, register map |
| `ti-ina219` | Texas Instruments INA219 — 26 V, 12-bit I²C monitor (alternative) | https://www.ti.com/product/INA219 · https://www.ti.com/lit/ds/symlink/ina219.pdf | comparison in the selection rationale |
| `espressif-devkitc` | Espressif ESP32-DevKitC-32E board documentation | https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/index.html | pinout, 3.3 V rail, logic levels |
| `espressif-esp32` | Espressif ESP32 series datasheet | https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf | GPIO capabilities, absolute maximum ratings |
| `bourns-mf-r` | Bourns MF-R PTC resettable fuse series | https://www.bourns.com/docs/product-datasheets/mf-r.pdf | hold and trip currents, voltage rating |
| `onsemi-ss34` | onsemi SS34 Schottky rectifier | https://www.onsemi.com/pdf/datasheet/ss34-d.pdf | forward drop, current and voltage rating |
| `littelfuse-smbj` | Littelfuse SMBJ TVS series | https://www.littelfuse.com/ | standoff and clamping voltage |
| `vishay-crcw2512` | Vishay CRCW series chip resistors | https://www.vishay.com/docs/20035/dcrcwe3.pdf | shunt tolerance, power rating, temperature coefficient |
| `yageo-rc` | Yageo RC series chip resistors | https://www.yageo.com/ | pull-up tolerance |
| `murata-grm` | Murata GRM ceramic capacitors | https://www.murata.com/en-global/products/capacitor/ceramiccapacitor | decoupling capacitor ratings |
| `kemet-c-series` | KEMET ceramic capacitors | https://www.kemet.com/en/us/capacitors/ceramic.html | decoupling capacitor ratings |
| `wurth-6130` | Würth WR-PHD 2.54 mm pin headers | https://www.we-online.com/en/components/products/WR-PHD | connector rating |
| `keystone-5000` | Keystone 5000 series test points | https://www.keyelco.com/ | test point part numbers |
| `manufacturer-terminal-blocks` | Phoenix Contact MKDS 1 series PCB terminal blocks | https://www.phoenixcontact.com/en-pc/terminal-blocks | connector current/voltage rating |

## How these figures were used

Every datasheet figure quoted in `design/dcm-hw-v1.json`, in `checks.py` output and
on the website is named with the document it came from. Where a number could not be
checked against an official document, it is marked as unverified rather than filled
in.

**Verify before selecting.** Component documentation changes. The person buying the
parts should re-read the current revision of each datasheet and record the revision
date beside the decision, the way `design-review.md` asks.
