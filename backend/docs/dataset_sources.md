Public dataset sources and access steps

1. NISR - Survey of Agricultural Production (SAS) / Agricultural Household Survey (AHS)
   - Contact NISR or check their data portal for public microdata access policies.
   - Many national surveys require a data request and a brief research plan.

2. CHIRPS (rainfall)
   - https://www.chc.ucsb.edu/data/chirps
   - Provides historical precipitation at high spatial resolution; useful for growing-season totals.

3. ERA5 / Copernicus
   - https://cds.climate.copernicus.eu
   - Reanalysis data for temperature, precipitation, and evapotranspiration.

4. Sentinel-2 / MODIS (NDVI)
   - Sentinel-2: https://scihub.copernicus.eu/ or via AWS/Open Data
   - MODIS: https://lpdaac.usgs.gov

5. Soil maps
   - ISRIC SoilGrids: https://soilgrids.org
   - AfSIS: https://africasoils.net

Access steps:
- Identify target variables (district-level yields, crop codes matching SAS catalog).
- File formats: microdata CSV / Stata. Use `pandas` and `pyreadstat` for Stata.
- For remote sensing and weather, download tiles or use cloud-hosted APIs and aggregate to district geometries.
