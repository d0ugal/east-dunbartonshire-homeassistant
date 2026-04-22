# Changelog

## [0.3.3](https://github.com/d0ugal/east-dunbartonshire-homeassistant/compare/v0.3.2...v0.3.3) (2026-04-22)


### Bug Fixes

* add BINARY_SENSOR and GEO_LOCATION to _Platform stub ([4812eca](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/4812ecac71266b15185ad8111e264f880d6908d4))
* restore blank line between stdlib and local imports ([312f5b6](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/312f5b625e1995be65af0a670305284097ab6fd4))

## [0.3.2](https://github.com/d0ugal/east-dunbartonshire-homeassistant/compare/v0.3.1...v0.3.2) (2026-04-21)


### Bug Fixes

* apply ruff formatting ([9e324ae](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/9e324ae988430ae421483c00c3fb6429fa6451a9))
* extract cutoff_ms to avoid ruff line-length violation ([0f195e9](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/0f195e95a568d0d3de62b2cb21223a1cef050721))
* filter planning applications to last 90 days via DATEMODIFIED ([5d2e0a3](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/5d2e0a35d7bee98cfc0d154859cb52eeb3bebdf2))
* use datetime.UTC alias (UP017) ([6dda37b](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/6dda37b554215ed413703a9924bb5fc74d927171))


### Documentation

* add example planning application automations to README ([6bc1d91](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/6bc1d9178e5143cdf0ea2f236cffe28128192954))
* add planning applications and geo location to README ([7783533](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/7783533b24dfd6dddd690d2e9f41f20d0e31be75))

## [0.3.1](https://github.com/d0ugal/east-dunbartonshire-homeassistant/compare/v0.3.0...v0.3.1) (2026-04-21)


### Bug Fixes

* add brown and blue bin types to BIN_TYPES ([fb5df9a](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/fb5df9a993d4415cf36b5025c84205f2c98bc6cb))

## [0.3.0](https://github.com/d0ugal/east-dunbartonshire-homeassistant/compare/v0.2.0...v0.3.0) (2026-04-21)


### Features

* planning application map pins via geo_location platform ([2b9535d](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/2b9535dfd54de58a1330f3cd9e55d6206e6e092e))


### Bug Fixes

* ruff format - collapse expressions that fit on one line ([f7aaadd](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/f7aaaddbd05b6040942a9eac66115adf3cd86e84))

## [0.2.0](https://github.com/d0ugal/east-dunbartonshire-homeassistant/compare/v0.1.0...v0.2.0) (2026-04-21)


### Features

* add daily integration tests against live council websites ([f2f5a9a](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/f2f5a9a2bb93345fa29412668e30d8bd27430b18))
* add school holidays calendars, binary sensors, and years sensor ([fb24786](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/fb247861d323a39181d79b25d2ab1567dcae3514))
* planning applications sensor with proximity filtering ([0e7e368](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/0e7e368a4a728a1717c0ae5e64f0a4191be7965e))
* rename scottish_bins to uk_bins throughout ([7ce217b](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/7ce217b19c01096b97d84343c16e72f5489f0bc1))
* rename to east_dunbartonshire, broaden scope beyond bins ([8b4432d](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/8b4432da21ae3b3290beb214a3a1e09de754e4e5))


### Bug Fixes

* add issues:write permission to integration test workflow ([57af8df](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/57af8df003f68bc6bd92ef3618da4f9d8cb57e71))
* remove invalid content_in_root field from hacs.json ([9523c92](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/9523c92467077bdfcbf9d45ef6e1e7c85c2d1c9e))
* replace placeholder icon with East Dunbartonshire Council logo ([1abd46b](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/1abd46b90b87ce5f4a632d9a90b0fb686fa667e7))
* west lothian JSON-RPC unwrap, GOSSForms user-agent, better test postcodes ([3d67672](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/3d67672873e928814a39888890e6de51ae96657d))


### Documentation

* update README for UK scope ([a1b25f0](https://github.com/d0ugal/east-dunbartonshire-homeassistant/commit/a1b25f00ba10b9dd9509cb8421cc75e51231d4bd))

## [0.1.0](https://github.com/d0ugal/scottish-bins-homeassistant/compare/v0.0.1...v0.1.0) (2026-04-20)


### Features

* add East Renfrewshire and South Ayrshire council support ([811f266](https://github.com/d0ugal/scottish-bins-homeassistant/commit/811f26646354e7e0e3a083f51aac10dc2d624676))
* add Falkirk council support; add council table to README ([e0d5005](https://github.com/d0ugal/scottish-bins-homeassistant/commit/e0d5005e2382b66217d2717a29ccb064ee66032b))
* add North Ayrshire and West Lothian council support ([9b9103f](https://github.com/d0ugal/scottish-bins-homeassistant/commit/9b9103f2b44874a95d7cdf5d774e2dd0a12de494))


### Bug Fixes

* move imports to top of test file, remove unused BinCollection import ([485e7b2](https://github.com/d0ugal/scottish-bins-homeassistant/commit/485e7b2bc2c0f00377b0d4e07f0ccf9f52ae18ac))


### Documentation

* add council implementation notes ([e995f81](https://github.com/d0ugal/scottish-bins-homeassistant/commit/e995f81c4351da83b71797c3d360ec6288711992))
