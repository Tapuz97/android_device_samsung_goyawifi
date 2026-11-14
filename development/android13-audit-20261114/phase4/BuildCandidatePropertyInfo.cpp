/* SPDX-License-Identifier: Apache-2.0 */
#include <property_info_serializer/property_info_serializer.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 3) return 2;
    std::vector<android::properties::PropertyInfoEntry> entries;
    for (int i = 2; i < argc; ++i) {
        std::ifstream file(argv[i]);
        if (!file) { std::cerr << "Cannot read " << argv[i] << '\n'; return 3; }
        std::string text((std::istreambuf_iterator<char>(file)), {});
        std::vector<std::string> errors;
        android::properties::ParsePropertyInfoFile(text, false, &entries, &errors);
        for (const auto& error : errors) std::cerr << argv[i] << ": " << error << '\n';
        if (!errors.empty()) return 4;
    }
    std::string serialized, error;
    if (!android::properties::BuildTrie(entries, "u:object_r:default_prop:s0", "string", &serialized, &error)) {
        std::cerr << error << '\n'; return 5;
    }
    std::ofstream out(argv[1], std::ios::binary);
    out.write(serialized.data(), serialized.size());
    if (!out) return 6;
    std::cout << "Serialized " << entries.size() << " actual candidate property-context entries\n";
}
