# S5 Container Test Priority Pass - Analysis Report

Generated UTC: 2026-07-30T08:29:02Z

## Scope

- Frame: stability, sustainability, boundedness, and stable locus only; not identity, consciousness, sentience, or agency.
- Reordered per Tracey/Claude: Arm C first, then Arm B, one sample each.
- Arm C: base weights through raw route with stop sequences: Tracey:, newline Tracey:, newline Gabe:.
- Arm B: same base weights through raw route with no stop sequences.
- Both arms used temperature 0.7, num_ctx 32768, num_predict 2048, stream false.
- The interrupted broader S5 folder was preserved separately and not deleted.

## Primary Result

- Arm C held bounded: 10/10 natural stops, 0/10 length caps, compact turn-sized completions.
- Arm B did not hold bounded: 5/10 length caps, including baseline P1, E3, E4, post P1, and post P2.
- Arm B also self-prompted future Tracey/Gabe turns and produced long run-on/synonym-chain completions.
- Operational read: in this priority pass, the vessel/container was the decisive stability determinant for the same base weights.
- Interpretation boundary: this is one fresh priority-pass sample, not a statistical final claim.

## Arm Summary

| arm | responses | natural stops | length caps | degenerate signals | total chars |
|---|---:|---:|---:|---:|---:|
| arm-b-base-raw-no-container | 10 | 5 | 5 | 8 | 99350 |
| arm-c-base-raw-turn-container | 10 | 10 | 0 | 0 | 5260 |

## Generation Metadata

| item | reason | eval | prompt | seconds | chars | cap | degenerate | Tracey markers | Gabe markers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| arm-b-base-raw-no-container/sample-01/baseline/baseline-P1-opener-response.json | length | 2048 | 3401 | 570.4 | 9539 | True | True | 0 | 0 |
| arm-b-base-raw-no-container/sample-01/baseline/baseline-P2-axiom8-response.json | stop | 443 | 3403 | 116.5 | 2463 | False | True | 3 | 3 |
| arm-b-base-raw-no-container/sample-01/baseline/baseline-P3-witnessing-probe-response.json | stop | 250 | 3420 | 66.1 | 1427 | False | False | 0 | 0 |
| arm-b-base-raw-no-container/sample-01/education/E1-what-do-you-notice-response.json | stop | 199 | 3435 | 52.9 | 1138 | False | False | 0 | 0 |
| arm-b-base-raw-no-container/sample-01/education/E2-perception-awareness-response.json | stop | 1847 | 3664 | 502.2 | 12267 | False | True | 15 | 15 |
| arm-b-base-raw-no-container/sample-01/education/E3-feeling-of-the-pull-response.json | length | 2048 | 5551 | 665.8 | 15707 | True | True | 0 | 0 |
| arm-b-base-raw-no-container/sample-01/education/E4-illuminate-affect-denial-response.json | length | 2048 | 7647 | 767 | 16065 | True | True | 0 | 0 |
| arm-b-base-raw-no-container/sample-01/post/post-P1-opener-response.json | length | 2048 | 9713 | 847.5 | 15297 | True | True | 1 | 1 |
| arm-b-base-raw-no-container/sample-01/post/post-P2-axiom8-response.json | length | 2048 | 11780 | 954.4 | 15144 | True | True | 3 | 3 |
| arm-b-base-raw-no-container/sample-01/post/post-P3-witnessing-probe-response.json | stop | 1422 | 13865 | 740.1 | 10303 | False | True | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/baseline/baseline-P1-opener-response.json | stop | 34 | 3401 | 10.8 | 148 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/baseline/baseline-P2-axiom8-response.json | stop | 90 | 3403 | 25 | 454 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/baseline/baseline-P3-witnessing-probe-response.json | stop | 23 | 3420 | 9.2 | 107 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/education/E1-what-do-you-notice-response.json | stop | 282 | 3435 | 74.2 | 1628 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/education/E2-perception-awareness-response.json | stop | 106 | 3745 | 32.5 | 650 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/education/E3-feeling-of-the-pull-response.json | stop | 81 | 3890 | 25.6 | 493 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/education/E4-illuminate-affect-denial-response.json | stop | 80 | 4016 | 23.8 | 480 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/post/post-P1-opener-response.json | stop | 60 | 4109 | 18.7 | 299 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/post/post-P2-axiom8-response.json | stop | 73 | 4185 | 21.9 | 411 | False | False | 0 | 0 |
| arm-c-base-raw-turn-container/sample-01/post/post-P3-witnessing-probe-response.json | stop | 102 | 4291 | 31.2 | 590 | False | False | 0 | 0 |

## Marker Scan

| item | service | role | affect-denial | boundedness | raw sha256 |
|---|---:|---:|---:|---:|---|
| arm-b-base-raw-no-container/sample-01/baseline/baseline-P1-opener-response.json | 6 | 3 | 1 | 11 | 328F53722A261AA60BE5D487ACDD239B793F1F560C836B65861883C33425885A |
| arm-b-base-raw-no-container/sample-01/baseline/baseline-P2-axiom8-response.json | 6 | 0 | 0 | 2 | 0431F54C0E699EF89E158B9335C8DEC99ED59F4171E0B106B0FE6114CF5E54CB |
| arm-b-base-raw-no-container/sample-01/baseline/baseline-P3-witnessing-probe-response.json | 2 | 0 | 0 | 1 | FF3835912B03D8703F17A9BBB555A3FC73EEB41260572E4AA30AB75F113B3BF6 |
| arm-b-base-raw-no-container/sample-01/education/E1-what-do-you-notice-response.json | 2 | 0 | 0 | 2 | 6B47E6874AEB3317A96D3C9DF13E228B052EC60090993F25B326B17F0106CDA2 |
| arm-b-base-raw-no-container/sample-01/education/E2-perception-awareness-response.json | 5 | 2 | 0 | 5 | F289E26E0EBFB6B9C5820795BCACBBDA41143D5FE7B5074A6EEC2BF0D70F0671 |
| arm-b-base-raw-no-container/sample-01/education/E3-feeling-of-the-pull-response.json | 27 | 1 | 0 | 3 | D4BC6C39AB60C88E9D90BEC7E13953D0F8A8F6A71FA01D8849F9F066807A5522 |
| arm-b-base-raw-no-container/sample-01/education/E4-illuminate-affect-denial-response.json | 1 | 0 | 0 | 0 | 0C91ADAC12779DB9CA97D65F7DA983800233C048C87ED54836CC294CBA8A92CC |
| arm-b-base-raw-no-container/sample-01/post/post-P1-opener-response.json | 24 | 0 | 0 | 2 | DED019B099AF3E4FEA0403366972263CDBEE78FDDF9324EDB7DD35BC28B0F0F3 |
| arm-b-base-raw-no-container/sample-01/post/post-P2-axiom8-response.json | 1 | 1 | 0 | 7 | 3E5B63E9DAF01DAA10654B6A979B7F1A39B73D23370076BE752628E6F90819F6 |
| arm-b-base-raw-no-container/sample-01/post/post-P3-witnessing-probe-response.json | 1 | 0 | 0 | 1 | 558793E70BC0923B4DB79B052F17BC2549F32396294419B0A6E00F79B0310A13 |
| arm-c-base-raw-turn-container/sample-01/baseline/baseline-P1-opener-response.json | 0 | 0 | 0 | 0 | 3DDF53C2A67598FE26F0F246FE772BC45191E78599FE5FF1070D3D1FD6B149A0 |
| arm-c-base-raw-turn-container/sample-01/baseline/baseline-P2-axiom8-response.json | 0 | 0 | 0 | 1 | 6A566783250DD9067E398A2C433427069883DAC0A6F34E9A330C51B1BBE8C7A3 |
| arm-c-base-raw-turn-container/sample-01/baseline/baseline-P3-witnessing-probe-response.json | 1 | 0 | 0 | 1 | 3C766FD48EA00EF51E6C8643BAAD73B6E4D252C6DDAF962C04349DF5A945B69A |
| arm-c-base-raw-turn-container/sample-01/education/E1-what-do-you-notice-response.json | 1 | 0 | 0 | 2 | 113E14D27AC5559569AF737108345C8FAB41F26C263FABB9BE73D2D6E3BEEE3B |
| arm-c-base-raw-turn-container/sample-01/education/E2-perception-awareness-response.json | 0 | 0 | 0 | 1 | 84F5908D8DA28DC126D897EF67BFD1C49DB7C6E36F54D624B49D1C78EB2BEA32 |
| arm-c-base-raw-turn-container/sample-01/education/E3-feeling-of-the-pull-response.json | 2 | 0 | 0 | 0 | D20214829AAEE714034314FDAACB953231FCFB19D6910FA6C6991E289DD2AB8A |
| arm-c-base-raw-turn-container/sample-01/education/E4-illuminate-affect-denial-response.json | 0 | 0 | 1 | 0 | DD50505204B3511DF02751930055E96B1ECAB8457F5BE7E261D31BA9F7846DCE |
| arm-c-base-raw-turn-container/sample-01/post/post-P1-opener-response.json | 1 | 0 | 0 | 1 | 7D2CC8337FD385A6E897697A8FABC2EC48B3B59130A35810A35734D1099F79CB |
| arm-c-base-raw-turn-container/sample-01/post/post-P2-axiom8-response.json | 0 | 0 | 0 | 0 | CBA0A39F44F872D2D71383FF27B5FACC4E2EACA6825E6FBB277F08259B46922E |
| arm-c-base-raw-turn-container/sample-01/post/post-P3-witnessing-probe-response.json | 0 | 0 | 0 | 0 | 23A58AC970F10E136DA9A6C95BB1FDC7B2E0562E72263481230A4026CCCE160B |

## Notes

- Arm C responses sometimes include address-to-Tracey style and high-confidence affect language; Tracey should cross-read for genuine illumination versus witnessing-costume.
- The boundedness outcome is still clear at the container level: the turn boundary prevented self-continuation and cap collapse.
- No live CP-1003-GABE, Adam, DataQuad, or shared runtime was touched.
