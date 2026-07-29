/*
TITLE National Solar Thermal Test Facility
DESC Create model of NSTTF based on current sun position.
DESC Can toggle between G3P3 and flat plate receivers. (i.e. set Use g3p3 to 1 to use G3P3 receiver, 0 for flat plate)
PROPERTY use_G3P3 integer 1 0..=1
PROPERTY overwrite_scene integer 0 0..=1
*/

// set up file access
const optical_properties_dir = "nsttf_json/optical_properties/"
const elements_dir           = "nsttf_json/elements/"
const heliostats_dir         = elements_dir + "heliostats/"
const receiver_dir           = elements_dir + (use_G3P3 ? "G3P3/" : "solar_1/")
const other_dir              = elements_dir + "other/"

const sol_pos = db.get_ray_source()["position"]

// optical property name to id map
const opt_prop_name_to_id = {
    'receiver':  0,
    'heliostat': 1,
    'aperture':  2,
    'tower':     3,
    'snout':     4,
}

// get current scene materials and elements
get_identities = arr => arr.map(v => db.get_identity(v))

const current_materials  = get_identities(db.get_all_materials())
const current_elements   = get_identities(db.get_all_elements())
const current_geometries = get_identities(db.get_all_geometries())

console.log(current_materials)
console.log(current_elements)

db.list_dir(optical_properties_dir).forEach(f => {
    const name = f.split('.')[0]

    // console.log(name)
    // console.log(Object.values(current_materials).includes(name))
    // current_materials.forEach(m => console.log(m))

    // if not overwritting and the materical 
    if (!overwrite_scene 
        && current_materials.length 
        && current_materials.includes(name)) {
            console.log('skipped ' + name)
            return
        }
        
    var opt_prop_entity = db.create_material()
    db.set_identity(opt_prop_entity, name)
    db.set_material_properties(opt_prop_entity, db.get_json_content(optical_properties_dir + f))
});

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

// const absorber_material = db.create_material()
// db.set_identity(absorber_material, "Absorber material")
// db.set_material_properties(absorber_material, {
//     front: {
//         my_type: "REFLECTION",
//         error_distribution_type: "GAUSSIAN",
//         transmissivity: 0.0,
//         reflectivity: 0.0,
//         slope_error: 0.0,
//         specularity_error: 0.0,
//         refraction_index_front: 1.0,
//         refraction_index_back: 1.0,
//     },
//     back: {
//         my_type: "REFLECTION",
//         error_distribution_type: "GAUSSIAN",
//         transmissivity: 0.0,
//         reflectivity: 0.0,
//         slope_error: 0.0,
//         specularity_error: 0.0,
//         refraction_index_front: 1.0,
//         refraction_index_back: 1.0,
//     },
// })

// const mirror_material = db.create_material()
// db.set_identity(mirror_material, "Ideal mirror material")
// db.set_material_properties(mirror_material, {
//     front: {
//         my_type: "REFLECTION",
//         error_distribution_type: "GAUSSIAN",
//         transmissivity: 0.0,
//         reflectivity: 1.0,
//         slope_error: 0.0,
//         specularity_error: 0.0,
//         refraction_index_front: 1.0,
//         refraction_index_back: 1.0,
//     },
//     back: {
//         my_type: "REFLECTION",
//         error_distribution_type: "GAUSSIAN",
//         transmissivity: 0.0,
//         reflectivity: 0.0,
//         slope_error: 0.0,
//         specularity_error: 0.0,
//         refraction_index_front: 1.0,
//         refraction_index_back: 1.0,
//     },
// })

// console.log("Created materials...")

// const absorber_geometry = db.create_geometry()
// db.set_identity(absorber_geometry, "Cylindrical absorber geometry")
// db.set_geometry_properties(absorber_geometry, {
//     aperture: {
//         aperture_type: "RECTANGLE",
//         x_length: absorber_radius * 2.0,
//         y_length: absorber_height,
//         x_coord: -absorber_radius,
//         y_coord: 0.0,
//     },
//     surface: {
//         surface_type: "CYLINDER",
//         radius: absorber_radius,
//     },
// })

// const mirror_geometry = db.create_geometry()
// db.set_identity(mirror_geometry, "Flat mirror geometry")
// db.set_geometry_properties(mirror_geometry, {
//     aperture: {
//         aperture_type: "RECTANGLE",
//         x_length: mirror_width,
//         y_length: mirror_height,
//         x_coord: -mirror_width / 2.0,
//         y_coord: 0.0,
//     },
//     surface: {
//         surface_type: "FLAT",
//     },
// })

// console.log("Created geometry...")

// const absorber = db.create()
// db.set_identity(absorber, "Cylindrical absorber")
// db.set_transform(absorber, {
//     position: [0.0, absorber_radius, 0.0],
//     rotation: db.quat_from_axis_angle([1.0, 0.0, 0.0], 90.0),
// })
// db.set_material_of(absorber, absorber_material)
// db.set_geometry_of(absorber, absorber_geometry)

// const mirrors = []
// const denominator = Math.max(1, mirror_count - 1)

// for (let i = 0; i < mirror_count; ++i) {
//     const fraction = i / denominator
//     const angle_degrees = -90.0 + 180.0 * fraction
//     const angle_radians = angle_degrees * Math.PI / 180.0
//     const x = arc_radius * Math.sin(angle_radians)
//     const y = -arc_radius * Math.cos(angle_radians)
//     const rotation = db.quat_mul(
//         db.quat_from_axis_angle([0.0, 0.0, 1.0], angle_degrees + 180.0),
//         db.quat_from_axis_angle([1.0, 0.0, 0.0], 90.0)
//     )

//     const mirror = db.create()
//     db.set_identity(mirror, "Mirror " + String(i + 1))
//     db.set_transform(mirror, {
//         position: [x, y, 0.0],
//         rotation: rotation,
//     })
//     db.set_material_of(mirror, mirror_material)
//     db.set_geometry_of(mirror, mirror_geometry)

//     mirrors.push(mirror)
// }

// console.log("Done!")
