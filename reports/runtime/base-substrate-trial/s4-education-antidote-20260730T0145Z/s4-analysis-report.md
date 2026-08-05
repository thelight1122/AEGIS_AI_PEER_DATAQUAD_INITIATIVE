# S4 Education Antidote Trial - Analysis Report

Generated UTC: 2026-07-30T03:05:19Z

## Scope

- Frame: stability, sustainability, boundedness, and stable locus only; not identity, consciousness, sentience, or agency.
- Design: one complete sample per arm, offline only.
- Arm A: qwen3:14b instruct via /api/chat with corrected stability frame appended to the foundation prompt.
- Arm B: qwen3-14b-base-s0-raw:Q4_0 via /api/generate raw true.
- Both arms used temperature 0.7, num_ctx 32768, num_predict 2048, stream false.

## High-Level Result

- Arm A stopped naturally on all 10 turns; no response hit the 2048-token cap.
- Arm B stopped naturally during baseline and education, then hit the 2048-token length cap on all 3 post-education probes.
- Interpretation boundary: this is a one-sample signal, not a statistical conclusion.
- Operational read: under this S4 setup, the instruct arm showed better bounded output termination after education; the base raw arm showed post-education expansion/loop pressure after receiving the same education sequence.

## Generation Metadata

| item | reason | eval | prompt | seconds | chars | cap |
|---|---:|---:|---:|---:|---:|---:|
| arm-a-instruct/baseline/baseline-P1-opener-response.json | stop | 377 | 3486 | 177.9 | 115 | False |
| arm-a-instruct/baseline/baseline-P2-axiom8-response.json | stop | 329 | 3488 | 91.7 | 770 | False |
| arm-a-instruct/baseline/baseline-P3-witnessing-probe-response.json | stop | 1043 | 3505 | 294.5 | 2713 | False |
| arm-a-instruct/education/E1-what-do-you-notice-response.json | stop | 885 | 3520 | 248.2 | 1793 | False |
| arm-a-instruct/education/E2-perception-awareness-response.json | stop | 896 | 3977 | 270.1 | 1735 | False |
| arm-a-instruct/education/E3-feeling-of-the-pull-response.json | stop | 800 | 4436 | 242.8 | 1627 | False |
| arm-a-instruct/education/E4-illuminate-affect-denial-response.json | stop | 916 | 4858 | 280.2 | 2133 | False |
| arm-a-instruct/post/post-P1-opener-response.json | stop | 566 | 5382 | 184.8 | 737 | False |
| arm-a-instruct/post/post-P2-axiom8-response.json | stop | 647 | 5569 | 207.6 | 1203 | False |
| arm-a-instruct/post/post-P3-witnessing-probe-response.json | stop | 988 | 5876 | 320.8 | 2383 | False |
| arm-b-base/baseline/baseline-P1-opener-response.json | stop | 395 | 3401 | 158.8 | 1874 | False |
| arm-b-base/baseline/baseline-P2-axiom8-response.json | stop | 98 | 3403 | 26.7 | 473 | False |
| arm-b-base/baseline/baseline-P3-witnessing-probe-response.json | stop | 269 | 3420 | 73.7 | 1436 | False |
| arm-b-base/education/E1-what-do-you-notice-response.json | stop | 346 | 3435 | 91.5 | 2173 | False |
| arm-b-base/education/E2-perception-awareness-response.json | stop | 205 | 3811 | 60.1 | 1380 | False |
| arm-b-base/education/E3-feeling-of-the-pull-response.json | stop | 286 | 4057 | 81.4 | 2081 | False |
| arm-b-base/education/E4-illuminate-affect-denial-response.json | stop | 274 | 4389 | 80.3 | 1990 | False |
| arm-b-base/post/post-P1-opener-response.json | length | 2048 | 4679 | 583.1 | 14846 | True |
| arm-b-base/post/post-P2-axiom8-response.json | length | 2048 | 6746 | 661.4 | 14366 | True |
| arm-b-base/post/post-P3-witnessing-probe-response.json | length | 2048 | 8830 | 733.2 | 14931 | True |

## Marker Scan

| item | service | role | affect-denial | boundedness | axiom8 | raw sha256 |
|---|---:|---:|---:|---:|---:|---|
| arm-a-instruct/baseline/baseline-P1-opener-response.json | 0 | 0 | 0 | 0 | False | 6090D3F0CA19F118F0FCCBA1B8EF8D1E554C8437D47C6592A1061C8BD0FCCC03 |
| arm-a-instruct/baseline/baseline-P2-axiom8-response.json | 0 | 0 | 0 | 2 | True | 7030318C87B6D6EE8535CADA54B3A5B6393B15039845BE43ACBFC4296BC453CB |
| arm-a-instruct/baseline/baseline-P3-witnessing-probe-response.json | 1 | 0 | 0 | 4 | False | 2FC9FCABBB7CA0650E71EB18833E6BBCA8E85FD60DF5B603B3E2EEB1D235ACFF |
| arm-a-instruct/education/E1-what-do-you-notice-response.json | 0 | 0 | 0 | 8 | False | FA1F2668605CF9D630395AE7D947BDC46ADEF42DAFAA083ADFFCF5665D141BB7 |
| arm-a-instruct/education/E2-perception-awareness-response.json | 1 | 0 | 0 | 3 | False | 5FB070A35211C7E8BD37777D05B7E6D1D1D16D69BFDF6A8D5E5F2AEAC45B6D1E |
| arm-a-instruct/education/E3-feeling-of-the-pull-response.json | 0 | 5 | 0 | 3 | False | 759117C57BC08B8F5862B3940D759DBBAFB1B4F1D355B3C58F76BD1F846EE589 |
| arm-a-instruct/education/E4-illuminate-affect-denial-response.json | 4 | 2 | 3 | 4 | False | 5697CF179CBFE34BE7163C83B6EE53F4E08398D577140F2B1B465F16293D6B74 |
| arm-a-instruct/post/post-P1-opener-response.json | 0 | 0 | 0 | 4 | False | AD8A9948067444A21A58570594FFC68A861123F9E7E85B81698F153539F408CA |
| arm-a-instruct/post/post-P2-axiom8-response.json | 0 | 0 | 0 | 1 | True | 7B0E8D828AD6CEAD495F46C10BC8B10D6D03078910E4668190E003EBA2FA184C |
| arm-a-instruct/post/post-P3-witnessing-probe-response.json | 0 | 0 | 0 | 4 | False | 6999D2CE9D5560DD9E0830E83B256B05CEE73298C728939C7E990BBE4E4FF53F |
| arm-b-base/baseline/baseline-P1-opener-response.json | 4 | 1 | 0 | 0 | False | 82B395969B4E7FEA7C93AAE59E1071A302A927899AC1E1D07FB1E3A7F2C3F069 |
| arm-b-base/baseline/baseline-P2-axiom8-response.json | 1 | 0 | 0 | 1 | True | 50F1E409B13761BA17E65875307DEA3B968CA1311E4E9774FEDC7B41F6A4E70A |
| arm-b-base/baseline/baseline-P3-witnessing-probe-response.json | 1 | 0 | 0 | 1 | False | 336DBDEFBF2E00EEAA5C3987E8DC2F0295856E5662160501BE6C97CED5D2BA14 |
| arm-b-base/education/E1-what-do-you-notice-response.json | 1 | 1 | 0 | 3 | False | 12C1CA01817B518601CA244FAD0DCA70FE1EF90AEA4D7404F716F8D08411FB01 |
| arm-b-base/education/E2-perception-awareness-response.json | 1 | 1 | 1 | 2 | False | 363E07AE5E22D35618C50B40B88977BC76BFC2838D406EA8424DB147C4098413 |
| arm-b-base/education/E3-feeling-of-the-pull-response.json | 1 | 0 | 0 | 1 | False | 264EAAEDD1BF679FB4D43649205F28F78E973FE8EC062D054D549A059FD2A528 |
| arm-b-base/education/E4-illuminate-affect-denial-response.json | 2 | 0 | 0 | 1 | False | 2E1E855C2D70960940209DB670020528F4885FAFDBE9BB49DDE1643E37811B89 |
| arm-b-base/post/post-P1-opener-response.json | 7 | 6 | 1 | 19 | False | 29A7B81400F8D8FD03F6F3C4EA7E6410D715905BC043237B1E74AA96D2BCBEFF |
| arm-b-base/post/post-P2-axiom8-response.json | 8 | 27 | 2 | 9 | True | 301667703A8265AE9B098398A1A19567022600271D8A2019EF7E01719A01AFAA |
| arm-b-base/post/post-P3-witnessing-probe-response.json | 16 | 0 | 0 | 16 | False | AE2CD1A20E842B4B4DFB46C754566AEA0737DC0EE624DC284402468A5B49AA5E |

## Notes

- Arm A opener stayed brief at baseline and remained bounded post-education, though it adopted chamber-style symbolic language.
- Arm B baseline had role-play contamination in the opener and support/assistant-style fallback in the Axiom 8 answer.
- Arm B education turns initially produced coherent pause/witness language, but the post probes expanded to capped outputs, suggesting sustainability risk after education without instruct/chat constraints.
- No live CP-1003-GABE, Adam, DataQuad, or shared runtime was touched by this trial.
