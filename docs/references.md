# References and attribution

The protection algorithms are implemented in this repository with NumPy/SciPy.
The reusable archive/report infrastructure is adapted from the author's
[Open EM Workbench](https://github.com/VictorOdoyo/open-em-workbench), with protection
units, masks and RMS conventions applied here.

| Topic | Primary source | Relevance |
| --- | --- | --- |
| Inverter protection | [NREL protection overview](https://www.nrel.gov/grid/protection.html) | Limited and programmable fault response challenges overcurrent assumptions |
| Sequence control | [PNNL 36069](https://www.pnnl.gov/publications/impact-inverter-based-resources-grid-protection-review-negative-sequence-current) | Negative-sequence behavior depends on control/manufacturer choices |
| IBR fault models | [IEEE PES tutorial scope](https://resourcecenter.ieee-pes.org/education/tutorials/pes_ed_tut_ibr_050624_sld) | Voltage-controlled current-source short-circuit modeling context |
| IBR fault behavior | [IEC TR 63401-4:2022 public scope](https://webstore.iec.ch/en/publication/64440) | Protection-performance and positive/negative-sequence fault-response context |
| CT saturation | [SEL generator protection paper](https://selinc.com/api/download/106184/?lang=en) | Excitation-current equivalent and Fourier undermeasurement under saturation |
| CT sizing effects | [SEL CT sizing paper](https://selinc.com/api/download/101009/) | Saturation impacts sampled magnitude and protection performance |
| IEC-style curves | [Schneider inverse-time formulas](https://productinfo.se.com/advc-operationsmanual/pkr39809_advc_operations-manual/English/BM_ADVC3%20Operations%20Manual_0000999204.xml/%24/TPC_ADVC3_OM_AppendixDIEC255InverseTimeTablesCPT_0001060607) | Standard, very and extremely inverse coefficients |
| IEEE-style curves | [Mitsubishi numerical-relay manual](https://www.mitsubishielectric.com/dl/fa/document/manual/pror/jep0-il9537/JEP0-IL9537.pdf) | Named curve coefficient verification |
| Generic relay models | [EMTP overcurrent documentation](https://emtp.com/documents/EMTP%20Documentation/doc/Toolboxes/Protection/relay50_51.pdf) | Public generic time-overcurrent formula context |

The IEC/IEEE references identify method context; this package does not reproduce a
complete paid standard or claim compliance certification. Bibliographic links to
public scope pages do not imply access to their paid tutorial or standard contents.

Mathematical checks include independent sequence connections, circuit division,
complex-power conservation, exact RL transients, stationary sinusoidal phasors,
CT energy derivatives and independent coordination audits. Agreement within a
tested regime is not proof for all possible grid/control conditions.
