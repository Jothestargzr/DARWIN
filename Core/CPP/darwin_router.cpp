#include <iostream>
#include <string>
#include <regex>
#include <cstdlib>
#include "httplib.h"
#include "json.hpp"

using json = nlohmann::json;

// Calculate Structural Entropy: Ratio of structural characters to overall length
double calculateStructuralEntropy(const std::string& content) {
    if (content.empty()) return 0.0;
    
    // Count structural elements (HTML tags, JSON braces)
    size_t structural_chars = 0;
    for (char c : content) {
        if (c == '<' || c == '>' || c == '{' || c == '}' || c == '[' || c == ']') {
            structural_chars++;
        }
    }
    
    return static_cast<double>(structural_chars) / content.length();
}

int main() {
    httplib::Server svr;

    svr.Post("/v1/chat/completions", [](const httplib::Request &req, httplib::Response &res) {
        try {
            auto body = json::parse(req.body);
            std::string content = "";
            
            // Extract content from messages to analyze entropy
            if (body.contains("messages") && body["messages"].is_array()) {
                for (const auto& msg : body["messages"]) {
                    if (msg.contains("content") && msg["content"].is_string()) {
                        content += msg["content"].get<std::string>();
                    }
                }
            }

            double entropy = calculateStructuralEntropy(content);
            std::string target_model = "qwen-max";
            
            // If the payload is huge but highly structured (e.g. repetitive HTML), downgrade to qwen-plus
            if (content.length() > 15000 && entropy > 0.15) {
                target_model = "qwen-plus";
                std::cout << "[~] Low entropy massive payload detected (" << content.length() << " chars, " << entropy << " entropy). Routing to " << target_model << std::endl;
            } else {
                std::cout << "[^] High entropy/logic payload detected. Routing to " << target_model << std::endl;
            }
            
            body["model"] = target_model;

            // Forward to DashScope
            httplib::Client cli("https://dashscope-intl.aliyuncs.com");
            httplib::Headers headers;
            
            const char* api_key = std::getenv("DASHSCOPE_API_KEY");
            if (api_key) {
                headers.emplace("Authorization", std::string("Bearer ") + api_key);
            }
            headers.emplace("Content-Type", "application/json");

            auto dash_res = cli.Post("/compatible-mode/v1/chat/completions", headers, body.dump(), "application/json");
            
            if (dash_res) {
                res.status = dash_res->status;
                res.set_content(dash_res->body, "application/json");
            } else {
                res.status = 502;
                res.set_content("{\"error\": \"Failed to reach DashScope\"}", "application/json");
            }
        } catch (const std::exception& e) {
            res.status = 400;
            res.set_content(std::string("{\"error\": \"") + e.what() + "\"}", "application/json");
        }
    });

    std::cout << "🚀 DARWIN C++ AI Router Started on port 8000" << std::endl;
    svr.listen("0.0.0.0", 8000);
    
    return 0;
}
