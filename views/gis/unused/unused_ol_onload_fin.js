// Center the map.
// used by add_feature_map.html
map.setCenter(point.transform(proj4326, map.getProjectionObject()), zoom);
}
window.onload(initMap());
