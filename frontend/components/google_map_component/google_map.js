(() => {
  const mapElement = document.getElementById("map");
  const statusElement = document.getElementById("map-status");
  const levelStatusElement = document.getElementById("map-level-status");
  let latestArgs;
  let map;
  let infoWindow;
  let thematicData;
  let adminData;
  let markers = [];
  let adminLabelMarkers = [];
  let rsaOverlay;
  let rsaToggle;
  let boundaryRequest;
  let boundaryRefreshTimer;
  let currentBoundaryKey;
  let activeBoundaryLevel;
  let boundaryCache = new Map();

  function sendHeight(height) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:setFrameHeight",
      height,
    }, "*");
  }

  function setComponentValue(value) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:setComponentValue",
      value,
    }, "*");
  }

  function showStatus(message) {
    statusElement.textContent = message;
    statusElement.dataset.visible = "true";
    sendHeight(latestArgs?.height || 540);
  }

  function hideStatus() {
    statusElement.dataset.visible = "false";
  }

  function makeInfoContent(title, details) {
    const container = document.createElement("div");
    container.className = "map-info";
    const heading = document.createElement("h3");
    heading.textContent = title || "Map details";
    container.appendChild(heading);

    (details || []).forEach((detail) => {
      const line = document.createElement("p");
      const label = document.createElement("strong");
      label.textContent = `${detail.label}: `;
      line.append(label, document.createTextNode(detail.value ?? ""));
      container.appendChild(line);
    });
    return container;
  }

  function addRsaToggle(args) {
    if (rsaToggle) return;
    rsaToggle = document.createElement("button");
    rsaToggle.className = "rsa-toggle";
    rsaToggle.type = "button";
    rsaToggle.textContent = "RSA imagery";
    rsaToggle.setAttribute("aria-pressed", "false");
    rsaToggle.title = "Toggle Rwanda Space Agency orthomosaic overlay";
    rsaToggle.addEventListener("click", () => {
      if (rsaOverlay) {
        map.overlayMapTypes.clear();
        rsaOverlay = null;
        rsaToggle.setAttribute("aria-pressed", "false");
        return;
      }

      const tileTemplate = args.rsa_tiles;
      rsaOverlay = new google.maps.ImageMapType({
        name: "Rwanda Space Agency orthomosaic",
        tileSize: new google.maps.Size(256, 256),
        maxZoom: 23,
        opacity: 0.72,
        getTileUrl: (coordinate, zoom) => {
          const scale = 2 ** zoom;
          if (coordinate.y < 0 || coordinate.y >= scale) return null;
          const wrappedX = ((coordinate.x % scale) + scale) % scale;
          return tileTemplate
            .replace("{z}", String(zoom))
            .replace("{y}", String(coordinate.y))
            .replace("{x}", String(wrappedX));
        },
      });
      map.overlayMapTypes.push(rsaOverlay);
      rsaToggle.setAttribute("aria-pressed", "true");
    });
    map.controls[google.maps.ControlPosition.LEFT_TOP].push(rsaToggle);
  }

  function clearMapData() {
    markers.forEach((marker) => marker.setMap(null));
    markers = [];
    const features = [];
    thematicData.forEach((feature) => features.push(feature));
    features.forEach((feature) => thematicData.remove(feature));
  }

  function renderMarkers(markerData) {
    markerData.forEach((item) => {
      const position = { lat: item.lat, lng: item.lng };
      const marker = new google.maps.Marker({
        map,
        position,
        title: item.title,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 9,
          fillColor: item.color || "#0284c7",
          fillOpacity: 0.82,
          strokeColor: "#ffffff",
          strokeWeight: 2,
        },
      });
      marker.addListener("click", () => {
        infoWindow.setContent(makeInfoContent(item.title, item.details));
        infoWindow.open({ map, anchor: marker });
        if (item.id) setComponentValue({ zone_id: item.id });
      });
      markers.push(marker);
    });
  }

  function renderGeoJson(args) {
    if (!args.geojson) return;
    thematicData.addGeoJson(args.geojson);
    thematicData.setStyle((feature) => ({
      fillColor: feature.getProperty("style_color") || "#94a3b8",
      fillOpacity: feature.getProperty("has_observations") ? 0.72 : 0.22,
      strokeColor: "#ffffff",
      strokeWeight: 1.6,
    }));

    if (args.fit_bounds) {
      const bounds = new google.maps.LatLngBounds();
      thematicData.forEach((feature) => {
        feature.getGeometry().forEachLatLng((latLng) => bounds.extend(latLng));
      });
      if (!bounds.isEmpty()) map.fitBounds(bounds);
    }
  }

  function getBoundaryLevel(zoom) {
    return [...(latestArgs.boundary_levels || [])]
      .sort((left, right) => left.min_zoom - right.min_zoom)
      .filter((level) => zoom >= level.min_zoom)
      .at(-1);
  }

  function getFeatureCenter(geometry) {
    const coordinates = [];
    function collect(value) {
      if (!Array.isArray(value)) return;
      if (value.length >= 2 && Number.isFinite(value[0]) && Number.isFinite(value[1])) {
        coordinates.push(value);
        return;
      }
      value.forEach(collect);
    }
    collect(geometry?.coordinates);
    if (!coordinates.length) return null;

    const bounds = new google.maps.LatLngBounds();
    coordinates.forEach(([lng, lat]) => bounds.extend({ lat, lng }));
    const center = bounds.getCenter();
    return { lat: center.lat(), lng: center.lng() };
  }

  function clearBoundaryLabels() {
    adminLabelMarkers.forEach((marker) => marker.setMap(null));
    adminLabelMarkers = [];
  }

  function showBoundaryDetails(event) {
    const properties = event.feature;
    const details = ["province", "district", "sector", "cell", "village"]
      .map((field) => ({
        label: field[0].toUpperCase() + field.slice(1),
        value: properties.getProperty(field),
      }))
      .filter((detail) => detail.value);
    infoWindow.setContent(makeInfoContent(
      properties.getProperty(activeBoundaryLevel?.name_field) || "Administrative area",
      details,
    ));
    infoWindow.setPosition(event.latLng);
    infoWindow.open({ map });
  }

  function renderBoundaryLabels(features, level) {
    clearBoundaryLabels();
    if (features.length > 250) {
      levelStatusElement.textContent =
        `${level.name} boundaries · ${features.length} areas · zoom in for labels · NISR 2022`;
      return;
    }

    features.forEach((feature) => {
      const center = getFeatureCenter(feature.geometry);
      const name = feature.properties?.[level.name_field];
      if (!center || !name) return;
      adminLabelMarkers.push(new google.maps.Marker({
        map,
        position: center,
        title: String(name),
        clickable: false,
        optimized: true,
        zIndex: google.maps.Marker.MAX_ZINDEX,
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
          fontWeight: "700",
        },
      }));
    });
    levelStatusElement.textContent =
      `${level.name} boundaries · ${features.length} areas · NISR 2022`;
  }

  function applyBoundaries(payload, level) {
    activeBoundaryLevel = level;
    const features = payload.features || [];
    const previousFeatures = [];
    adminData.forEach((feature) => previousFeatures.push(feature));
    previousFeatures.forEach((feature) => adminData.remove(feature));
    clearBoundaryLabels();

    if (features.length) {
      adminData.addGeoJson(payload);
      renderBoundaryLabels(features, level);
    } else {
      levelStatusElement.textContent = `${level.name} boundaries · no areas in this view · NISR 2022`;
    }
  }

  function buildBoundaryQuery(level, bounds) {
    const url = new URL(
      `${latestArgs.boundaries_url}/${level.service}/FeatureServer/${level.layer_id}/query`,
    );
    const parameters = {
      where: "1=1",
      outFields: level.fields.join(","),
      returnGeometry: "true",
      outSR: "4326",
      geometry: `${bounds.west},${bounds.south},${bounds.east},${bounds.north}`,
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
    window.clearTimeout(boundaryRefreshTimer);
    boundaryRefreshTimer = window.setTimeout(refreshAdministrativeBoundaries, 300);
  }

  async function refreshAdministrativeBoundaries() {
    if (!map || !latestArgs?.boundary_levels?.length) return;
    const level = getBoundaryLevel(map.getZoom());
    const mapBounds = map.getBounds();
    if (!level || !mapBounds) return;

    const extent = mapBounds.toJSON();
    const bounds = {
      west: extent.west,
      south: extent.south,
      east: extent.east,
      north: extent.north,
    };
    const roundedBounds = {
      west: Math.floor(bounds.west * 100) / 100 - 0.005,
      south: Math.floor(bounds.south * 100) / 100 - 0.005,
      east: Math.ceil(bounds.east * 100) / 100 + 0.005,
      north: Math.ceil(bounds.north * 100) / 100 + 0.005,
    };
    const requestKey = `${level.name}:${Object.values(roundedBounds).join(",")}`;
    if (requestKey === currentBoundaryKey) return;
    currentBoundaryKey = requestKey;

    if (boundaryRequest) boundaryRequest.abort();
    boundaryRequest = null;
    const cached = boundaryCache.get(requestKey);
    if (cached) {
      applyBoundaries(cached, level);
      return;
    }

    const previousFeatures = [];
    adminData.forEach((feature) => previousFeatures.push(feature));
    previousFeatures.forEach((feature) => adminData.remove(feature));
    clearBoundaryLabels();
    boundaryRequest = new AbortController();
    const requestController = boundaryRequest;
    levelStatusElement.textContent = `Loading ${level.name.toLowerCase()} boundaries · NISR 2022`;

    try {
      const response = await fetch(buildBoundaryQuery(level, roundedBounds), {
        signal: requestController.signal,
      });
      if (!response.ok) throw new Error(`Boundary service returned HTTP ${response.status}`);
      const payload = await response.json();
      if (payload.error) {
        throw new Error(payload.error.message || "Boundary service returned an error");
      }
      if (requestController !== boundaryRequest) return;

      boundaryCache.set(requestKey, payload);
      if (boundaryCache.size > 24) {
        boundaryCache.delete(boundaryCache.keys().next().value);
      }
      applyBoundaries(payload, level);
      if (payload.exceededTransferLimit) {
        levelStatusElement.textContent += " · zoom in to load all areas";
      }
    } catch (error) {
      if (error.name === "AbortError") return;
      if (requestController !== boundaryRequest) return;
      levelStatusElement.textContent =
        `${level.name} boundaries unavailable · check connection · NISR 2022`;
      console.error("Unable to load Rwanda administrative boundaries", error);
    }
  }

  function installMapInteractions() {
    thematicData.addListener("mouseover", (event) => {
      thematicData.overrideStyle(event.feature, {
        strokeColor: "#0f172a",
        strokeWeight: 3,
        fillOpacity: 0.86,
      });
    });
    thematicData.addListener("mouseout", (event) => thematicData.revertStyle(event.feature));
    thematicData.addListener("click", (event) => {
      const properties = event.feature;
      const details = [
        { label: "Province", value: properties.getProperty("province") },
        { label: "Observed value", value: properties.getProperty("metric_value") },
        { label: "Observed range", value: properties.getProperty("observed_range") },
        { label: "Records", value: properties.getProperty("record_count") },
      ].filter((detail) => detail.value);
      infoWindow.setContent(makeInfoContent(properties.getProperty("district"), details));
      infoWindow.setPosition(event.latLng);
      infoWindow.open({ map });
    });
    adminData.addListener("mouseover", (event) => {
      adminData.overrideStyle(event.feature, {
        strokeColor: "#0f172a",
        strokeWeight: 2.5,
      });
    });
    adminData.addListener("mouseout", (event) => adminData.revertStyle(event.feature));
    adminData.addListener("click", showBoundaryDetails);
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
        zoomControl: true,
        clickableIcons: false,
      });
      infoWindow = new google.maps.InfoWindow();
      thematicData = new google.maps.Data({ map });
      adminData = new google.maps.Data({ map });
      adminData.setStyle({
        fillColor: "#0f766e",
        fillOpacity: 0.035,
        strokeColor: "#0f766e",
        strokeOpacity: 0.85,
        strokeWeight: 1.15,
        clickable: true,
      });
      installMapInteractions();
      map.addListener("idle", scheduleBoundaryRefresh);
    }

    clearMapData();
    addRsaToggle(args);
    renderGeoJson(args);
    renderMarkers(args.markers || []);
    sendHeight(args.height || 540);
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
    window.gm_authFailure = () => {
      showStatus("Google Maps could not authorize this key. Check that the Maps JavaScript API and billing are enabled, and that this site is allowed by the key's referrer restrictions.");
    };

    const script = document.createElement("script");
    script.id = "google-maps-api";
    script.async = true;
    script.defer = true;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(args.api_key)}&callback=initGoogleMapsComponent&v=weekly`;
    script.onerror = () => showStatus("Google Maps could not load. Check the network and the configured API key.");
    document.head.appendChild(script);
  }

  window.addEventListener("message", (event) => {
    if (event.data?.type !== "streamlit:render") return;
    latestArgs = event.data.args || {};
    const height = Number(latestArgs.height) || 540;
    mapElement.style.height = `${height}px`;
    document.body.style.height = `${height}px`;
    sendHeight(height);

    if (!latestArgs.api_key) {
      showStatus("Google Maps is not configured. Set GOOGLE_MAPS_API_KEY in the frontend environment.");
      return;
    }
    loadGoogleMaps(latestArgs);
  });

  window.parent.postMessage({
    isStreamlitMessage: true,
    type: "streamlit:componentReady",
    apiVersion: 1,
  }, "*");
})();
