(() => {
  const mapElement = document.getElementById("map");
  const statusElement = document.getElementById("map-status");
  let latestArgs;
  let map;
  let infoWindow;
  let markers = [];
  let rsaOverlay;
  let rsaToggle;

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
    map.data.forEach((feature) => features.push(feature));
    features.forEach((feature) => map.data.remove(feature));
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
    map.data.addGeoJson(args.geojson);
    map.data.setStyle((feature) => ({
      fillColor: feature.getProperty("style_color") || "#94a3b8",
      fillOpacity: feature.getProperty("has_observations") ? 0.72 : 0.22,
      strokeColor: "#ffffff",
      strokeWeight: 1.6,
    }));

    if (args.fit_bounds) {
      const bounds = new google.maps.LatLngBounds();
      map.data.forEach((feature) => {
        feature.getGeometry().forEachLatLng((latLng) => bounds.extend(latLng));
      });
      if (!bounds.isEmpty()) map.fitBounds(bounds);
    }
  }

  function installMapInteractions() {
    map.data.addListener("mouseover", (event) => {
      map.data.overrideStyle(event.feature, {
        strokeColor: "#0f172a",
        strokeWeight: 3,
        fillOpacity: 0.86,
      });
    });
    map.data.addListener("mouseout", (event) => map.data.revertStyle(event.feature));
    map.data.addListener("click", (event) => {
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
      installMapInteractions();
    }

    clearMapData();
    addRsaToggle(args);
    renderGeoJson(args);
    renderMarkers(args.markers || []);
    sendHeight(args.height || 540);
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
