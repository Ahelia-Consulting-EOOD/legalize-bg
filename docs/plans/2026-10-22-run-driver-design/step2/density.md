## Round 0: tokens per call, per section and per block, by agent and sections per call

| Agent | Sections per call | Calls | Sections | Blocks | Median tokens per call | Tokens per section | Tokens per block | Exceptions per 100 blocks | Low confidence per 100 | Answer defects per 100 | Check failures per 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| labeller (lean) | 3 | 2 | 6 | 179 | 33,413 | 11,137 | 373 | 7.8 | 7.8 | 0.00 | 0.00 |
| labeller (lean) | 6 | 1 | 6 | 214 | 62,741 | 10,456 | 293 | 12.1 | 12.1 | 0.00 | 0.00 |
| labeller (lean) | 7 | 2 | 14 | 637 | 72,705 | 10,386 | 228 | 4.1 | 3.8 | 0.00 | 0.31 |
| labeller (lean) | 8 | 96 | 768 | 24622 | 61,414 | 7,676 | 239 | 0.9 | 0.9 | 0.01 | 0.01 |
| general-purpose(default) (night) | 1 | 82 | 82 | 3339 | 72,318 | 72,318 | 1,776 | 4.2 | 3.9 | 0.27 | 0.00 |
| general-purpose (night) | 1 | 2 | 2 | 48 | 71,531 | 71,531 | 2,980 | 14.6 | 14.6 | 0.00 | 0.00 |
| general-purpose (night) | 3 | 83 | 252 | 11893 | 86,972 | 28,990 | 614 | 0.7 | 0.7 | 0.00 | 0.01 |
| general-purpose (night) | 4 | 1 | 4 | 110 | 89,161 | 22,290 | 810 | 6.4 | 6.4 | 0.00 | 0.00 |
| general-purpose (night) | 8 | 14 | 102 | 3059 | 107,630 | 13,453 | 448 | 1.8 | 1.8 | 0.00 | 0.00 |

Tokens per call is the harness's figure for the whole subagent call (fixed context, instructions, tasks and answers, counted once). Tokens per block divides the median call by the mean blocks per section and the sections per call.

## Round 0: exceptions per 100 blocks by position within the call (calls of 8 sections)

| Agent | Position | Sections | Blocks | Exceptions per 100 blocks | Low confidence per 100 | Answer defects per 100 |
|---|---|---|---|---|---|---|
| labeller (lean) | 1 | 96 | 3216 | 1.1 | 1.1 | 0.00 |
| labeller (lean) | 2 | 96 | 3103 | 0.7 | 0.7 | 0.00 |
| labeller (lean) | 3 | 96 | 3117 | 1.0 | 1.0 | 0.00 |
| labeller (lean) | 4 | 96 | 3070 | 0.6 | 0.6 | 0.00 |
| labeller (lean) | 5 | 96 | 2955 | 1.0 | 1.0 | 0.07 |
| labeller (lean) | 6 | 96 | 2959 | 0.9 | 0.9 | 0.00 |
| labeller (lean) | 7 | 96 | 3121 | 0.9 | 0.9 | 0.00 |
| labeller (lean) | 8 | 96 | 3081 | 1.1 | 1.0 | 0.00 |
| general-purpose (night) | 1 | 14 | 461 | 0.0 | 0.0 | 0.00 |
| general-purpose (night) | 2 | 13 | 365 | 1.1 | 1.1 | 0.00 |
| general-purpose (night) | 3 | 13 | 383 | 1.8 | 1.8 | 0.00 |
| general-purpose (night) | 4 | 13 | 379 | 1.8 | 1.8 | 0.00 |
| general-purpose (night) | 5 | 13 | 396 | 1.8 | 1.8 | 0.00 |
| general-purpose (night) | 6 | 12 | 331 | 2.1 | 2.1 | 0.00 |
| general-purpose (night) | 7 | 12 | 362 | 2.8 | 2.8 | 0.00 |
| general-purpose (night) | 8 | 12 | 382 | 3.7 | 3.7 | 0.00 |

## Round 0: exceptions per 100 blocks by position within the call (calls of 3 sections)

| Agent | Position | Sections | Blocks | Exceptions per 100 blocks | Low confidence per 100 | Answer defects per 100 |
|---|---|---|---|---|---|---|
| labeller (lean) | 1 | 2 | 50 | 10.0 | 10.0 | 0.00 |
| labeller (lean) | 2 | 2 | 52 | 7.7 | 7.7 | 0.00 |
| labeller (lean) | 3 | 2 | 77 | 6.5 | 6.5 | 0.00 |
| general-purpose (night) | 1 | 84 | 3928 | 0.6 | 0.6 | 0.00 |
| general-purpose (night) | 2 | 84 | 3998 | 0.6 | 0.6 | 0.00 |
| general-purpose (night) | 3 | 84 | 3967 | 0.9 | 0.9 | 0.00 |

## Per act: exceptions per 100 blocks by density (round 0)

| Act | Sections per call | Sections | Blocks | Exceptions per 100 blocks |
|---|---|---|---|---|
| danachno-osiguritelen-protsesualen-kodeks | 6 | 6 | 214 | 12.1 |
| danachno-osiguritelen-protsesualen-kodeks | 8 | 152 | 5345 | 1.5 |
| grazhdanski-protsesualen-kodeks | 3 | 3 | 91 | 15.4 |
| grazhdanski-protsesualen-kodeks | 8 | 128 | 3727 | 0.5 |
| kodeks-na-targovskoto-koraboplavane-zagl-izm-dv- | 3 | 75 | 2059 | 0.1 |
| kodeks-na-targovskoto-koraboplavane-zagl-izm-dv- | 4 | 4 | 110 | 6.4 |
| kodeks-na-targovskoto-koraboplavane-zagl-izm-dv- | 7 | 7 | 249 | 6.4 |
| kodeks-na-targovskoto-koraboplavane-zagl-izm-dv- | 8 | 1 | 27 | 0.0 |
| kodeks-na-truda | 3 | 6 | 177 | 5.6 |
| kodeks-na-truda | 8 | 101 | 3032 | 1.8 |
| kodeks-za-sotsialno-osiguryavane-zagl-izm-dv-br- | 8 | 192 | 6343 | 0.5 |
| konstitutsiya-na-republika-balgariya | 1 | 15 | 615 | 0.8 |
| nakazatelen-kodeks | 3 | 78 | 2996 | 1.8 |
| naredba-04-14-ot-9-oktomvri-2019-g-za-usloviyata | 1 | 9 | 554 | 5.2 |
| naredba-1-ot-1-avgust-2013-g-za-usloviyata-i-red | 1 | 14 | 663 | 0.2 |
| naredba-5-ot-10-may-1999-g-za-strukturata-na-zap | 1 | 1 | 41 | 0.0 |
| naredba-5-ot-10-may-1999-g-za-strukturata-na-zap | 3 | 78 | 5989 | 0.1 |
| pravilnik-za-organizatsiyata-i-deynostta-na-naro | 1 | 1 | 7 | 100.0 |
| pravilnik-za-organizatsiyata-i-deynostta-na-naro | 3 | 18 | 760 | 2.0 |
| targovski-zakon | 8 | 184 | 5267 | 1.1 |
| zakon-za-danak-varhu-dobavenata-stoynost | 7 | 7 | 388 | 2.6 |
| zakon-za-danak-varhu-dobavenata-stoynost | 8 | 112 | 3940 | 1.0 |
| zakon-za-izplashtane-na-zadalzheniyata-ugovoreni | 1 | 1 | 3 | 100.0 |
| zakon-za-obshtestveniya-transport | 1 | 17 | 572 | 0.0 |
| zakon-za-zadalzheniyata-i-dogovorite | 1 | 26 | 932 | 10.8 |
