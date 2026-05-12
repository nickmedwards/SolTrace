#include <cstdint>
#include <map>
#include <string>
#include <vector>

// #include "element.hpp"

// #include <../../hpvm.h>

// SimulationResult headers
#include "group_result.hpp"

namespace SolTrace::Result
{
    GroupResult::GroupResult(int8_t group_id, size_t n_groups) : 
        group_id(group_id),
        absorb_count(0),
        reflect_count(0),
        transmit_count(0),
        virtual_count(0),
        absorb_sun_previous(0),
        reflect_sun_previous(0),
        transmit_sun_previous(0),
        virtual_sun_previous(0)
    {
        // need extra spots in the vectors for ungrouped elements and the sun.
        absorb_previous_group.resize(n_groups);
        reflect_previous_group.resize(n_groups);
        transmit_previous_group.resize(n_groups);
        virtual_previous_group.resize(n_groups);
    }

    void GroupResult::write_json(nlohmann::ordered_json &jnode) const
    {
        jnode["group_id"] = group_id;
        jnode["absorb_count"] = absorb_count;
        jnode["reflect_count"] = reflect_count;
        jnode["transmit_count"] = transmit_count;
        jnode["virtual_count"] = virtual_count;
        jnode["absorb_sun_previous"] = absorb_sun_previous;
        jnode["reflect_sun_previous"] = reflect_sun_previous;
        jnode["transmit_sun_previous"] = transmit_sun_previous;
        jnode["virtual_sun_previous"] = virtual_sun_previous;
        jnode["absorb_previous_group"] = absorb_previous_group;
        jnode["reflect_previous_group"] = reflect_previous_group;
        jnode["transmit_previous_group"] = transmit_previous_group;
        jnode["virtual_previous_group"] = virtual_previous_group;
    }
}