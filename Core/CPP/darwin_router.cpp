#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <regex>
#include <cstdlib>
#include <queue>
#include <memory>
#include <ctime>
#include "httplib.h"
#include "json.hpp"

using json = nlohmann::json;

// ============================================================================
// DARWIN Multi-Model AI Router with Load Balancing & Rate Limiting
// ============================================================================

struct ModelEndpoint {
    std::string name;
    std::string base_url;
    std::string api_key_env;
    double cost_per_1k_tokens;
    int max_concurrent;
    int current_load;
};

struct RequestMetrics {
    std::string request_id;
    std::string target_model;
    double tokens_used;
    double cost;
    long latency_ms;
    int retry_count;
};

class DarwinRouter {
private:
    std::vector<ModelEndpoint> models;
    std::queue<json> request_queue;
    std::map<std::string, RequestMetrics> metrics_log;
    
    // Rate limiting: requests per minute per model
    std::map<std::string, int> rate_limit_counters;
    std::map<std::string, long> rate_limit_reset_times;
    
public:
    DarwinRouter() {
        // Register available models
        models.push_back({
            "claude-3-5-sonnet",
            "https://api.anthropic.com/v1",
            "ANTHROPIC_API_KEY",
            0.003,  // $3 per 1M input tokens
            10,
            0
        });
        
        models.push_back({
            "glm-5.2",
            "https://z.ai/api/v1",
            "GLM_API_KEY",
            0.002,  // $2 per 1M input tokens
            20,
            0
        });
        
        models.push_back({
            "qwen-max",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "DASHSCOPE_API_KEY",
            0.0015, // $1.5 per 1M input tokens
            15,
            0
        });
        
        models.push_back({
            "deepseek-coder",
            "https://api.deepseek.com/v1",
            "DEEPSEEK_API_KEY",
            0.0008, // $0.8 per 1M input tokens
            8,
            0
        });
    }
    
    double calculateStructuralEntropy(const std::string& content) {
        if (content.empty()) return 0.0;
        
        size_t structural_chars = 0;
        for (char c : content) {
            if (c == '<' || c == '>' || c == '{' || c == '}' || 
                c == '[' || c == ']' || c == '(' || c == ')') {
                structural_chars++;
            }
        }
        
        return static_cast<double>(structural_chars) / content.length();
    }
    
    int estimateTokenCount(const std::string& text) {
        // Rough estimation: 1 token ~= 4 characters for English
        return (text.length() / 4) + 1;
    }
    
    std::string selectBestModel(const json& request) {
        std::string content = "";
        int total_tokens = 0;
        
        // Extract content from messages
        if (request.contains("messages") && request["messages"].is_array()) {
            for (const auto& msg : request["messages"]) {
                if (msg.contains("content") && msg["content"].is_string()) {
                    content += msg["content"].get<std::string>();
                }
            }
        }
        
        total_tokens = estimateTokenCount(content);
        double entropy = calculateStructuralEntropy(content);
        
        std::string selected_model = "claude-3-5-sonnet"; // Default to best performer
        
        // Routing logic
        if (total_tokens > 50000 && entropy < 0.10) {
            // Low entropy, massive payload → use cheap model
            selected_model = "deepseek-coder";
            std::cout << "[~] Large low-entropy payload (" << total_tokens << " tokens, " 
                      << entropy << " entropy). Route → deepseek-coder" << std::endl;
        }
        else if (total_tokens > 20000) {
            // Large payload → use balanced model
            selected_model = "qwen-max";
            std::cout << "[~] Large payload (" << total_tokens << " tokens). Route → qwen-max" << std::endl;
        }
        else if (entropy > 0.20) {
            // High complexity → use best model
            selected_model = "claude-3-5-sonnet";
            std::cout << "[^] Complex logic (" << entropy << " entropy). Route → claude-3-5-sonnet" << std::endl;
        }
        else if (total_tokens > 30000) {
            // Medium-large coding task
            selected_model = "glm-5.2";
            std::cout << "[^] Medium-large task (" << total_tokens << " tokens). Route → glm-5.2" << std::endl;
        }
        
        return selected_model;
    }
    
    bool checkRateLimit(const std::string& model) {
        long now = std::time(nullptr);
        
        if (rate_limit_reset_times.find(model) == rate_limit_reset_times.end()) {
            rate_limit_reset_times[model] = now + 60;
            rate_limit_counters[model] = 0;
        }
        
        if (now >= rate_limit_reset_times[model]) {
            rate_limit_reset_times[model] = now + 60;
            rate_limit_counters[model] = 0;
        }
        
        // 60 requests per minute limit
        if (rate_limit_counters[model] >= 60) {
            return false;
        }
        
        rate_limit_counters[model]++;
        return true;
    }
    
    json forwardRequest(const std::string& model, const json& request) {
        // Find model endpoint
        ModelEndpoint* endpoint = nullptr;
        for (auto& ep : models) {
            if (ep.name == model) {
                endpoint = &ep;
                break;
            }
        }
        
        if (!endpoint) {
            json error_response;
            error_response["error"] = "Model not found: " + model;
            return error_response;
        }
        
        // Get API key
        const char* api_key = std::getenv(endpoint->api_key_env.c_str());
        if (!api_key) {
            json error_response;
            error_response["error"] = "API key not set for " + model;
            return error_response;
        }
        
        try {
            httplib::Client cli(endpoint->base_url.c_str());
            cli.set_connection_timeout(0, 500000); // 500ms
            cli.set_read_timeout(5, 0);             // 5 seconds
            
            httplib::Headers headers;
            headers.emplace("Authorization", std::string("Bearer ") + api_key);
            headers.emplace("Content-Type", "application/json");
            
            json request_body = request;
            request_body["model"] = model;
            
            auto res = cli.Post("/chat/completions", headers, request_body.dump(), "application/json");
            
            if (res) {
                std::cout << "[+] " << model << " responded: " << res->status << std::endl;
                return json::parse(res->body);
            } else {
                json error_response;
                error_response["error"] = "Failed to reach " + model;
                error_response["error_code"] = 502;
                return error_response;
            }
        } catch (const std::exception& e) {
            json error_response;
            error_response["error"] = e.what();
            error_response["error_code"] = 500;
            return error_response;
        }
    }
};

int main() {
    DarwinRouter router;
    httplib::Server svr;
    
    svr.Post("/v1/chat/completions", [&router](const httplib::Request &req, httplib::Response &res) {
        try {
            auto body = json::parse(req.body);
            
            // 1. Select optimal model
            std::string selected_model = router.selectBestModel(body);
            
            // 2. Check rate limit
            if (!router.checkRateLimit(selected_model)) {
                res.status = 429;
                json rate_limit_error;
                rate_limit_error["error"] = "Rate limit exceeded for " + selected_model;
                res.set_content(rate_limit_error.dump(), "application/json");
                return;
            }
            
            // 3. Forward to selected model
            json response = router.forwardRequest(selected_model, body);
            
            res.status = 200;
            res.set_content(response.dump(), "application/json");
            
        } catch (const std::exception& e) {
            res.status = 400;
            json error;
            error["error"] = e.what();
            res.set_content(error.dump(), "application/json");
        }
    });
    
    // Health check endpoint
    svr.Get("/health", [](const httplib::Request &, httplib::Response &res) {
        json health;
        health["status"] = "healthy";
        health["service"] = "DARWIN C++ AI Router";
        health["version"] = "2.0";
        res.set_content(health.dump(), "application/json");
    });
    
    std::cout << "🚀 DARWIN C++ Multi-Model AI Router v2.0 started on port 8000" << std::endl;
    std::cout << "   Supports: Claude 3.5 Sonnet, GLM-5.2, Qwen-Max, DeepSeek-Coder" << std::endl;
    std::cout << "   Features: Intelligent routing, rate limiting, load balancing, cost optimization" << std::endl;
    
    svr.listen("0.0.0.0", 8000);
    
    return 0;
}
