#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include "httplib.h"
#include "json.hpp"

using json = nlohmann::json;

std::vector<std::string> micro_action_buffer;

void flush_to_terminus() {
    if (micro_action_buffer.empty()) return;

    httplib::Client cli("http://localhost:6363");
    cli.set_basic_auth("admin", "root");

    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    std::string timestamp = std::to_string(ms);
    std::string state_id = "PhaseState/cpp_mcp_" + timestamp;

    std::string compressed_action = "Agent executed " + std::to_string(micro_action_buffer.size()) + " semantic micro-actions.";
    
    json action_state = {
        {"@type", "PhaseState"},
        {"@id", state_id},
        {"timestamp", timestamp},
        {"accumulated_energy", 5.0},
        {"current_action", compressed_action}
    };
    
    json documents = json::array();
    documents.push_back(action_state);

    auto res = cli.Post("/api/document/admin/darwin?author=darwin_cpp_mcp", documents.dump(), "application/json");
    
    // Clear buffer after successful flush
    micro_action_buffer.clear();
}

void handle_request(const json& req) {
    json response = {
        {"jsonrpc", "2.0"},
        {"id", req.contains("id") ? req["id"] : nullptr}
    };

    std::string method = req.value("method", "");

    if (method == "initialize") {
        response["result"] = {
            {"protocolVersion", "2024-11-05"},
            {"capabilities", {{"tools", json::object()}}},
            {"serverInfo", {{"name", "darwin-cpp-mcp"}, {"version", "1.0.0"}}}
        };
    } 
    else if (method == "tools/list") {
        response["result"] = {
            {"tools", json::array({
                {
                    {"name", "log_phase_change"},
                    {"description", "Log an ontological capability phase to TerminusDB. Buffers micro-actions to prevent bloat."},
                    {"inputSchema", {
                        {"type", "object"},
                        {"properties", {
                            {"action", {{"type", "string"}, {"description", "The semantic action taken"}}},
                            {"is_boundary", {{"type", "boolean"}, {"description", "True if this completes a major task"}}}
                        }},
                        {"required", json::array({"action"})}
                    }}
                }
            })}
        };
    }
    else if (method == "tools/call") {
        auto params = req.value("params", json::object());
        std::string name = params.value("name", "");
        
        if (name == "log_phase_change") {
            auto args = params.value("arguments", json::object());
            std::string action = args.value("action", "unknown action");
            bool is_boundary = args.value("is_boundary", false);
            
            micro_action_buffer.push_back(action);
            
            if (is_boundary || micro_action_buffer.size() >= 5) {
                flush_to_terminus();
            }

            response["result"] = {
                {"content", json::array({
                    {{"type", "text"}, {"text", "Action buffered/logged successfully in C++ MCP."}}
                })}
            };
        }
    }
    else {
        // Unknown method
        response["error"] = {{"code", -32601}, {"message", "Method not found"}};
    }

    // JSON-RPC over stdio strictly requires writing JSON string followed by newline
    std::cout << response.dump() << "\n";
    std::cout.flush();
}

int main() {
    std::string line;
    // Loop continuously reading from stdin
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        
        try {
            json req = json::parse(line);
            handle_request(req);
        } catch (const json::parse_error& e) {
            json err = {
                {"jsonrpc", "2.0"},
                {"error", {{"code", -32700}, {"message", "Parse error"}}},
                {"id", nullptr}
            };
            std::cout << err.dump() << "\n";
            std::cout.flush();
        }
    }
    return 0;
}
