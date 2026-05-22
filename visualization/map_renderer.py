"""
TRACE - Interactive Map Renderer using Folium
"""
import folium
import geopandas as gpd
import pandas as pd
import json
from folium.plugins import MarkerCluster


def render_map(gdf, output_path, title="TRACE Speed Safety Score"):
    """
    Render interactive Folium map with:
    - Color-coded road segments by SSS
    - Click popup with full decomposition
    - Layer control by priority
    - Legend
    """
    # Reproject to WGS84 for Folium
    gdf_map = gdf.copy()
    if gdf_map.crs and gdf_map.crs.to_epsg() != 4326:
        gdf_map = gdf_map.to_crs(epsg=4326)

    # Calculate map center
    bounds = gdf_map.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=9,
        tiles='CartoDB positron'
    )

    # Add title
    title_html = f'''
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                z-index: 9999; background: white; padding: 8px 16px; 
                border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                font-family: Arial; font-size: 16px; font-weight: bold; color: #333;">
        {title}
    </div>'''
    m.get_root().html.add_child(folium.Element(title_html))

    # Create feature groups per priority
    p1_group = folium.FeatureGroup(name='P1: Immediate Review (Red)', show=True)
    p2_group = folium.FeatureGroup(name='P2: Secondary Review (Orange)', show=True)
    p3_group = folium.FeatureGroup(name='P3: Monitor (Yellow)', show=True)
    ok_group = folium.FeatureGroup(name='Acceptable (Green)', show=False)

    group_map = {
        'P1: Immediate Review': p1_group,
        'P2: Secondary Review': p2_group,
        'P3: Monitor': p3_group,
        'Acceptable': ok_group,
    }

    segments_added = 0
    for _, row in gdf_map.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue

        color = row.get('color', '#aaaaaa')
        flag = row.get('priority_flag', 'Acceptable')
        sss = row.get('sss', 50)
        limit = row.get('SpeedLimit', 'N/A')
        v85 = row.get('F85thPercentileSpeed', 'N/A')
        t1 = row.get('t1_score', 'N/A')
        t2 = row.get('t2_score', 'N/A')
        t3 = row.get('t3_score', 'N/A')
        vru_t = row.get('t3_vru_threshold', 'N/A')
        eis = row.get('t2_eis_range', 'N/A')
        explanation = row.get('explanation', '')
        road_name = row.get('english_ro') or row.get('names_primary') or row.get('EnglishRoadName') or 'Unnamed'
        road_class = row.get('RoadClass', 'N/A')
        land_use = row.get('LandUse', 'N/A')

        popup_html = f"""
        <div style="font-family:Arial; font-size:13px; min-width:280px; max-width:320px;">
            <b style="font-size:14px;">{road_name}</b><br>
            <span style="color:{color}; font-weight:bold;">
                {flag}
            </span>
            <hr style="margin:6px 0;">
            <b>Speed Safety Score: {sss:.0f} / 100</b>
            <table style="width:100%; margin-top:6px; border-collapse:collapse;">
                <tr style="background:#f5f5f5;">
                    <td style="padding:3px;"><b>Tier 1</b> Speed Alignment</td>
                    <td style="padding:3px; text-align:right;
                        color:{'red' if isinstance(t1,float) and t1<50 else 'green'};">
                        {f'{t1:.0f}' if isinstance(t1,(int,float)) else t1}
                    </td>
                </tr>
                <tr>
                    <td style="padding:3px;"><b>Tier 2</b> Environment</td>
                    <td style="padding:3px; text-align:right;
                        color:{'red' if isinstance(t2,float) and t2<50 else 'green'};">
                        {f'{t2:.0f}' if isinstance(t2,(int,float)) else t2}
                    </td>
                </tr>
                <tr style="background:#f5f5f5;">
                    <td style="padding:3px;"><b>Tier 3</b> VRU Protection</td>
                    <td style="padding:3px; text-align:right;
                        color:{'red' if isinstance(t3,float) and t3<50 else 'green'};">
                        {f'{t3:.0f}' if isinstance(t3,(int,float)) else t3}
                    </td>
                </tr>
            </table>
            <hr style="margin:6px 0;">
            <small>
            Posted limit: <b>{f'{limit:.0f} km/h' if isinstance(limit,(int,float)) and not pd.isna(limit) else 'No data'}</b> &nbsp;|&nbsp;
            V85: <b>{f'{v85:.0f} km/h' if isinstance(v85,(int,float)) and not pd.isna(v85) else 'No data'}</b><br>
            VRU threshold: {f'{vru_t:.0f} km/h' if isinstance(vru_t,(int,float)) else 'N/A'} &nbsp;|&nbsp;
            Env. implied: {eis} km/h<br>
            Class: {road_class} &nbsp;|&nbsp; Land use: {land_use}
            </small>
            <hr style="margin:6px 0;">
            <small style="color:#555;">{explanation}</small>
        </div>
        """

        try:
            coords = list(row.geometry.coords) if row.geometry.geom_type == 'LineString' \
                else [c for part in row.geometry.geoms for c in part.coords]
            latlons = [(lat, lon) for lon, lat in coords]

            line = folium.PolyLine(
                locations=latlons,
                color=color,
                weight=4 if flag == 'P1: Immediate Review' else 2.5,
                opacity=0.85,
                popup=folium.Popup(popup_html, max_width=340),
                tooltip=f"SSS: {sss:.0f} | {flag}"
            )
            group_map[flag].add_child(line)
            segments_added += 1
        except Exception:
            continue

    for grp in [p1_group, p2_group, p3_group, ok_group]:
        m.add_child(grp)

    folium.LayerControl(collapsed=False).add_to(m)

    # Legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; right: 20px; z-index: 9999;
                background: white; padding: 12px 16px; border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-family: Arial; font-size:13px;">
        <b>Speed Safety Score</b><br>
        <span style="color:#d62728;">&#9644;</span> P1 Immediate Review (&lt;40)<br>
        <span style="color:#ff7f0e;">&#9644;</span> P2 Secondary Review (40–60)<br>
        <span style="color:#bcbd22;">&#9644;</span> P3 Monitor (60–80)<br>
        <span style="color:#2ca02c;">&#9644;</span> Acceptable (&gt;80)
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(output_path)
    print(f"  Map saved: {output_path} ({segments_added} segments rendered)")
