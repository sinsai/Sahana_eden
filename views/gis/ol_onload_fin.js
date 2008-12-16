// Center the map.
map.setCenter(point.transform(proj4326, map.getProjectionObject()), zoom);
}
window.onload(initMap());
