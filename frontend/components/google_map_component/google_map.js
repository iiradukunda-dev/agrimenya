(() => {
  const mapElement = document.getElementById("map");
  const statusElement = document.getElementById("map-status");
  const levelStatusElement = document.getElementById("map-level-status");
  let latestArgs;
  let map;
  let infoWindow;
  let adminData;
  let labels = [];
  let activeBoundaryLevel;
  let boundaryRequest;
  let refreshTimer;
  let currentBoundaryKey;
  const boundaryCache = new Map();

  function sendMessage(type, payload) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type,
      ...payload,
    }, "*");
  }

  function showStatus(message) {
    statusElement.textContent = message;
    statusElement.dataset.visible = "true";
  }

  function hideStatus() {
    statusElement.dataset.visible = "false";
  }

  function getBoundaryLevel(zoom) {
    return [...(latestArgs.boundary_levels || [])]
      .sort((left, right) => left.min_zoom - right.min_zoom)
      .filter((level) => zoom >= level.min_zoom)
      .at(-1);
  }

  function clearLabels() {
    labels.forEach((marker) => marker.setMap(null));
    labels = [];
  }

  function showBoundaryDetails(event) {
    const feature = event.feature;
    const level = activeBoundaryLevel;
    const district = feature.getProperty("district");
    const sector = feature.getProperty("sector");
    const cell = feature.getProperty("cell");
    const name = feature.getProperty(level?.name_field);
    if (!district || !name) return;

    const location = { district: String(district) };
    const details = [];
    if (level.name === "Sector" && sector) {
      location.sector = String(sector);
      details.push(`Sector: ${String(sector)}`);
    } else if (level.name === "Cell" && sector && cell) {
      location.sector = String(sector);
      location.cell = String(cell);
      details.push(`Sector: ${String(sector)}`, `Cell: ${String(cell)}`);
    } else if (level.name === "District") {
      details.push(`District: ${String(district)}`);
    }
    if (!details.length) details.push(`${level.name}: ${String(name)}`);

    const content = document.createElement("div");
    content.textContent = details.join(" · ");
    infoWindow.setContent(content);
    infoWindow.setPosition(event.latLng);
    infoWindow.open({ map });
    if (["District", "Sector", "Cell"].includes(level.name)) {
      sendMessage("streamlit:setComponentValue", { value: { admin_location: location } });
    }

    const bounds = new google.maps.LatLngBounds();
    feature.getGeometry().forEachLatLng((point) => bounds.extend(point));
    if (bounds.isEmpty()) return;

    const nextZoom = { District: 10, Sector: 13, Cell: 16 }[level.name];
    map.fitBounds(bounds);
    google.maps.event.addListenerOnce(map, "idle", () => {
      if (map.getZoom() < nextZoom) map.setZoom(nextZoom);
    });
    levelStatusElement.textContent = `Selected ${name} · loading next boundary level · NISR 2022`;
  }

  function applyBoundaries(payload, level) {
    activeBoundaryLevel = level;
    const existing = [];
    adminData.forEach((feature) => existing.push(feature));
    existing.forEach((feature) => adminData.remove(feature));
    clearLabels();

    const features = payload.features || [];
    if (!features.length) {
      levelStatusElement.textContent = `${level.name} boundaries unavailable in this view · NISR 2022`;
      return;
    }
    adminData.addGeoJson(payload);
    if (features.length <= 250) {
      features.forEach((feature) => {
        const name = feature.properties?.[level.name_field];
        if (!name || !feature.geometry) return;
        const points = [];
        function collect(value) {
          if (!Array.isArray(value)) return;
          if (value.length >= 2 && Number.isFinite(value[0]) && Number.isFinite(value[1])) {
            points.push({ lat: value[1], lng: value[0] });
            return;
          }
          value.forEach(collect);
        }
        collect(feature.geometry.coordinates);
        if (!points.length) return;
        const bounds = new google.maps.LatLngBounds();
        points.forEach((point) => bounds.extend(point));
        const marker = new google.maps.Marker({
          map,
          position: bounds.getCenter(),
          title: String(name),
          clickable: false,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 0,
            fillOpacity: 0,
            strokeOpacity: 0,
          },
          label: {
            text: String(name),
            className: "admin-boundary-label",
            fontSize: level.name === "Village" ? "10px" : "11px",
          },
        });
        labels.push(marker);
      });
    }
    levelStatusElement.textContent =
      `${level.name} boundaries · ${features.length} areas · click an area to zoom · NISR 2022`;
    if (payload.exceededTransferLimit) levelStatusElement.textContent += " · zoom in to load all areas";
  }

  function buildBoundaryQuery(level, extent) {
    const url = new URL(
      `${latestArgs.boundaries_url}/${level.service}/FeatureServer/${level.layer_id}/query`,
    );
    const parameters = {
      where: "1=1",
      outFields: level.fields.join(","),
      returnGeometry: "true",
      outSR: "4326",
      geometry: `${extent.west},${extent.south},${extent.east},${extent.north}`,
      geometryType: "esriGeometryEnvelope",
      inSR: "4326",
      spatialRel: "esriSpatialRelIntersects",
      maxAllowableOffset: String(level.max_allowable_offset),
      resultRecordCount: "1000",
      f: "geojson",
    };
    Object.entries(parameters).forEach(([name, value]) => url.searchParams.set(name, value));
    return url;
  }

  function scheduleBoundaryRefresh() {
    window.clearTimeout(refreshTimer);
    refreshTimer = window.setTimeout(refreshBoundaries, 300);
  }

  async function refreshBoundaries() {
    if (!map || !latestArgs?.boundary_levels?.length) return;
    const level = getBoundaryLevel(map.getZoom());
    const bounds = map.getBounds();
    if (!level || !bounds) return;

    const extent = bounds.toJSON();
    const rounded = {
      west: Math.floor(extent.west * 100) / 100 - 0.005,
      south: Math.floor(extent.south * 100) / 100 - 0.005,
      east: Math.ceil(extent.east * 100) / 100 + 0.005,
      north: Math.ceil(extent.north * 100) / 100 + 0.005,
    };
    const key = `${level.name}:${Object.values(rounded).join(",")}`;
    if (key === currentBoundaryKey) return;
    currentBoundaryKey = key;
    if (boundaryRequest) boundaryRequest.abort();

    const cached = boundaryCache.get(key);
    if (cached) {
      applyBoundaries(cached, level);
      return;
    }
    const controller = new AbortController();
    boundaryRequest = controller;
    levelStatusElement.textContent = `Loading ${level.name.toLowerCase()} boundaries · NISR 2022`;
    try {
      const response = await fetch(buildBoundaryQuery(level, rounded), { signal: controller.signal });
      if (!response.ok) throw new Error(`NISR returned HTTP ${response.status}`);
      const payload = await response.json();
      if (payload.error) throw new Error(payload.error.message || "NISR boundary request failed");
      if (controller !== boundaryRequest) return;
      boundaryCache.set(key, payload);
      if (boundaryCache.size > 24) boundaryCache.delete(boundaryCache.keys().next().value);
      applyBoundaries(payload, level);
    } catch (error) {
      if (error.name === "AbortError" || controller !== boundaryRequest) return;
      console.error("Unable to load NISR administrative boundaries", error);
      levelStatusElement.textContent = `${level.name} boundaries unavailable · check connection · NISR 2022`;
    }
  }

  function renderMap(args) {
    hideStatus();
    if (!map) {
      map = new google.maps.Map(mapElement, {
        center: args.center,
        zoom: args.zoom,
        mapTypeId: args.map_type,
        mapTypeControl: true,
        mapTypeControlOptions: {
          mapTypeIds: ["roadmap", "satellite"],
          position: google.maps.ControlPosition.TOP_RIGHT,
        },
        streetViewControl: false,
        fullscreenControl: true,
        clickableIcons: false,
      });
      infoWindow = new google.maps.InfoWindow();
      adminData = new google.maps.Data({ map });
      adminData.setStyle({
        fillColor: "#0f766e",
        fillOpacity: 0.035,
        strokeColor: "#0f766e",
        strokeOpacity: 0.85,
        strokeWeight: 1.15,
        clickable: true,
      });
      adminData.addListener("click", showBoundaryDetails);
      adminData.addListener("mouseover", (event) => {
        adminData.overrideStyle(event.feature, { strokeColor: "#0f172a", strokeWeight: 2.5 });
      });
      adminData.addListener("mouseout", (event) => adminData.revertStyle(event.feature));
      map.addListener("idle", scheduleBoundaryRefresh);
    }
    scheduleBoundaryRefresh();
  }

  function loadGoogleMaps(args) {
    if (window.google?.maps) {
      renderMap(args);
      return;
    }
    if (document.getElementById("google-maps-api")) return;
    window.initGoogleMapsComponent = () => {
      if (latestArgs) renderMap(latestArgs);
    };
    window.gm_authFailure = () => showStatus(
      "Google Maps could not authorize this key. Check API access, billing, and referrer restrictions.",
    );
    const script = document.createElement("script");
    script.id = "google-maps-api";
    script.async = true;
    script.defer = true;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(args.api_key)}&callback=initGoogleMapsComponent&v=weekly`;
    script.onerror = () => showStatus("Google Maps could not load. Check the network and configured API key.");
    document.head.appendChild(script);
  }

  window.addEventListener("message", (event) => {
    if (event.data?.type !== "streamlit:render") return;
    latestArgs = event.data.args || {};
    const height = Number(latestArgs.height) || 580;
    mapElement.style.height = `${height}px`;
    document.body.style.height = `${height}px`;
    sendMessage("streamlit:setFrameHeight", { height });
    if (!latestArgs.api_key) {
      showStatus("Google Maps is not configured. Set GOOGLE_MAPS_API_KEY in the frontend environment.");
      return;
    }
    loadGoogleMaps(latestArgs);
  });

  sendMessage("streamlit:componentReady", { apiVersion: 1 });
})();
