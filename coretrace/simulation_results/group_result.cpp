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
        absorb_previous_group.resize(n_groups);
        reflect_previous_group.resize(n_groups);
        transmit_previous_group.resize(n_groups);
        virtual_previous_group.resize(n_groups);
    }
}