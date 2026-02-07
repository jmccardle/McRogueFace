#pragma once
#include "LdtkTypes.h"
#include <Python.h>

namespace mcrf {
namespace ldtk {

// Load an LDtk project from a .ldtk JSON file
std::shared_ptr<LdtkProjectData> loadLdtkProject(const std::string& path);

} // namespace ldtk
} // namespace mcrf
