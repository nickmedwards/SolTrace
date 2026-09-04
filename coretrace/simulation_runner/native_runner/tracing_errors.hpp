#ifndef SOLTRACE_TRACING_ERRORS_H
#define SOLTRACE_TRACING_ERRORS_H

#include "optical_properties.hpp"

#include "mtrand.hpp"
#include "native_runner_types.hpp"

namespace SolTrace::NativeRunner {

void Errors(MTRand& myrng,
            glm::dvec3& CosIn,
            int Source,
            TSun* Sun,
            // TElement *Element,
            // TOpticalProperties *OptProperties,
            SolTrace::Data::optical_set_ptr OptProperties,
            const bool LastHitBackSide,
            glm::dvec3& CosOut,
            glm::dvec3& DFXYZ);

void SurfaceNormalErrors(MTRand& myrng,
                         glm::dvec3& CosIn,
                         SolTrace::Data::optical_set_ptr OptProperties,
                         const bool LastHitBackSide,
                         glm::dvec3& CosOut) noexcept(false); // throw(nanexcept);


} // namespace SolTrace::NativeRunner

#endif
