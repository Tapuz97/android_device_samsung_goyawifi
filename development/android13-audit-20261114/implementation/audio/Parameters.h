/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include <cerrno>
#include <climits>
#include <cstdlib>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace android { namespace t110_audio_compat {
// A local key/value container, not an ABI replacement for Android AudioParameter.
// Preserve unrelated parameters and explicit routing keys when adding ANI7 keys.
class Parameters {
public:
    explicit Parameters(const char* pairs = "") {
        std::string input = pairs ? pairs : "";
        size_t pos = 0;
        while (pos < input.size()) {
            size_t end = input.find(';', pos);
            if (end == std::string::npos) end = input.size();
            std::string token = input.substr(pos, end-pos);
            size_t eq = token.find('=');
            if (eq != std::string::npos && eq != 0) set(token.substr(0,eq),token.substr(eq+1));
            pos = end+1;
        }
    }
    int getInt(const char* key, int& result) const {
        for (const auto& entry : entries) if (entry.first == key) {
            if (entry.second.empty()) return -EINVAL;
            char* end = nullptr; errno = 0;
            long long value = std::strtoll(entry.second.c_str(),&end,10);
            if (errno || *end || value < INT32_MIN || value > UINT32_MAX) return -EINVAL;
            result = static_cast<int32_t>(static_cast<uint32_t>(value));
            return 0;
        }
        return -ENOENT;
    }
    void addInt(const char* key, int value) { set(key,std::to_string(value)); }
    std::string toString() const {
        std::string output;
        for (const auto& entry : entries) {
            if (!output.empty()) output += ';';
            output += entry.first + '=' + entry.second;
        }
        return output;
    }
private:
    std::vector<std::pair<std::string,std::string>> entries;
    void set(std::string key,std::string value) {
        for (auto& entry : entries) if (entry.first == key) {entry.second=value;return;}
        entries.emplace_back(std::move(key),std::move(value));
    }
};
} }
