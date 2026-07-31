/*
TITLE National Solar Thermal Test Facility
DESC Create model of NSTTF based on current sun position.
DESC Can toggle between G3P3 and flat plate receivers. (i.e. set Use g3p3 to 1 to use G3P3 receiver, 0 for flat plate)
PROPERTY use_G3P3 integer 0 0..=1
PROPERTY overwrite_scene integer 0 0..=1
*/

// set up file access
const optical_properties_dir = "nsttf_json/optical_properties/"
const elements_dir           = "nsttf_json/elements/"
const heliostats_dir         = elements_dir + "heliostats/"
const receiver_dir           = elements_dir + (use_G3P3 ? "G3P3/" : "solar_1/")
const other_dir              = elements_dir + "other/"

const sol_pos = db.get_ray_source()["position"]

const opt_prop_id_to_name = ['receiver', 'heliostat', 'aperture', 'tower', 'snout']
// optical property name to id map
const opt_prop_name_to_id = opt_prop_id_to_name.reduce((accum, next, idx) => {accum[next] = idx; return accum;}, {})

// get current scene materials and elements
get_identities = arr => arr.map(v => db.get_identity(v))

const material_entities = [...db.get_all_materials()]
const element_entities  = [...db.get_all_elements()]
const geometry_entities = [...db.get_all_geometries()]

const material_identities = get_identities(material_entities)
const element_identities  = get_identities(element_entities)
const geometry_identities = get_identities(geometry_entities)

if (overwrite_scene) {
    // for (var ents in [material_entities, element_entities, geometry_entities]) {
    //     for (var ent in ents) db.destroy(ent);
    // }
    for (var ent in material_entities) db.destroy(ent);
    for (var ent in element_entities) db.destroy(ent);
    for (var ent in geometry_entities) db.destroy(ent);
    // material_entities.forEach(ent => db.destroy(ent))
    // element_entities.forEach(ent => db.destroy(ent))
    // geometry_entities.forEach(ent => db.destroy(ent))

    material_identities.length = 0
    element_identities.length  = 0
    geometry_identities.length = 0
    console.log('Destroyed current entities')
    
    const test = db.get_all_materials()
    console.log(test)
    console.log(test.length)
    test.forEach(e => console.log(db.valid(e)))
}



console.log(material_identities.length)
console.log(typeof material_identities)
console.log(element_identities.length)
console.log(typeof element_identities)

in_scene = (curr, rt, name) => curr.length && curr.includes(name) && rt.push(name)

function log_skipped(skipped, files, desc) {
    if (skipped.length === files.length) console.log(`Skipped adding ${desc}...`)
    else if (skipped.length > 0) console.log(
        skipped.reduce(
            (accum, next) => accum + ` ${next}`,
            `Skipped adding ${desc}:`
        ) + '...'
    )
}

const skipped = []

const optical_properties_files = db.list_dir(optical_properties_dir)

optical_properties_files.forEach(f => {
    const name = f.split('.')[0]

    // if not overwritting and the materical is in the scene already
    if (!overwrite_scene && in_scene(material_identities, skipped, name)) return
        
    const opt_prop_entity = db.create_material()
    db.set_identity(opt_prop_entity, name)
    db.set_material_properties(opt_prop_entity, db.get_json_content(optical_properties_dir + f))
});

log_skipped(skipped, optical_properties_files, 'optical properties')

skipped.length = 0

const receiver_files = db.list_dir(receiver_dir)

get_euler_deg = (v, zrot) => [180 * Math.atan2(v[0], v[2]) / Math.PI, 180 * Math.asin(v[1]) / Math.PI, zrot]

// intrinsic active rotation first by α around Z, 
// then β around the new X, finally γ around the new Z
euler_to_quat = euler => db.quat_mul(
    db.quat_mul(
        db.quat_from_axis_angle([0.0, 0.0, 1.0], euler[0]),
        db.quat_from_axis_angle([1.0, 0.0, 0.0], euler[1])
    ),
    db.quat_from_axis_angle([0.0, 0.0, 1.0], euler[2])
)

function get_rotation(origin, aim, zrot) {
    const dr = db.vec3_normalize(aim.map((a, idx) => a - origin[idx]))
    return euler_to_quat(get_euler_deg(dr, zrot))
}

receiver_files.forEach(f => {
    const name = f.split('.')[0]

    // if not overwritting and the element/geometry is in the scene already
    console.log(name)
    console.log(element_identities.includes(name))
    if (!overwrite_scene  && in_scene(element_identities, skipped, name)) return

    const receiver_json =  db.get_json_content(receiver_dir + f)

    const geometry = db.create_geometry()
    db.set_identity(geometry, `${name} geometry`)
    db.set_geometry_properties(geometry, {
        aperture: receiver_json['aperture'],
        surface: receiver_json['surface'],
    })
    
    const ent = db.create()
    db.set_identity(ent, name)
    db.set_transform(ent, {
        position: [...receiver_json['origin']],
        rotation: get_rotation([...receiver_json['origin']], [...receiver_json['aim']], receiver_json['zrot'])
    })
    db.set_material_of(ent, db.get_material_entity(opt_prop_id_to_name[receiver_json['opt_id']]))
    db.set_geometry_of(ent, geometry)
})

log_skipped(skipped, receiver_files, 'receiver elements')

// var test = db.get_json_content("nsttf_json/optical_properties/heliostat.json");
// console.log(Object.keys(test));
// const heliostat_material = db.create_material()
// db.set_identity(heliostat_material, test["my_name"])
// db.set_material_properties(heliostat_material, test)

console.log("Done.")

// test = db.list_dir("nsttf_json/optical_properties")
// console.log(test)

// test = db.get_all_materials()
// console.log(test)

// test.forEach(v => console.log(db.get_identity(v)))

// console.log(get_identities(test))
