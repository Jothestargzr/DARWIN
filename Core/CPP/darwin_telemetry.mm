#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
#include <iostream>
#include <string>
#include <chrono>
#include "httplib.h"
#include "json.hpp"

using json = nlohmann::json;
using namespace std::chrono;

void LogToTerminusDB(const std::string& appName) {
    httplib::Client cli("http://localhost:6363");
    
    // Auth: admin:root
    cli.set_basic_auth("admin", "root");
    
    auto now = system_clock::now();
    auto ms = duration_cast<milliseconds>(now.time_since_epoch()).count();
    std::string timestamp = std::to_string(ms);
    std::string state_id = "PhaseState/cpp_" + timestamp;
    
    json action_state = {
        {"@type", "PhaseState"},
        {"@id", state_id},
        {"timestamp", timestamp},
        {"accumulated_energy", 1.5},
        {"current_action", "Focus shifted to " + appName}
    };
    
    json documents = json::array();
    documents.push_back(action_state);
    
    std::string payload = documents.dump();
    std::string url = "/api/document/admin/darwin?author=darwin_cpp_telemetry&message=Logged%20Window%20Focus";
    
    auto res = cli.Post(url, payload, "application/json");
    if (res && res->status == 200) {
        std::cout << "[+] Logged telemetry: " << appName << std::endl;
    } else {
        std::cerr << "[-] TerminusDB sync failed: ";
        if (res) std::cerr << res->status;
        std::cerr << std::endl;
    }
}

@interface AppObserver : NSObject
@end

@implementation AppObserver
- (void)appActivated:(NSNotification *)notification {
    NSRunningApplication *app = [[notification userInfo] objectForKey:NSWorkspaceApplicationKey];
    if (app && app.localizedName) {
        std::string appName = std::string([app.localizedName UTF8String]);
        LogToTerminusDB(appName);
    }
}
@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        std::cout << "🚀 DARWIN C++ Telemetry Daemon Started (0% CPU Idle)" << std::endl;
        
        AppObserver *observer = [[AppObserver alloc] init];
        [[[NSWorkspace sharedWorkspace] notificationCenter] 
            addObserver:observer 
               selector:@selector(appActivated:) 
                   name:NSWorkspaceDidActivateApplicationNotification 
                 object:nil];
                 
        // Log the initial app
        NSRunningApplication *frontmost = [[NSWorkspace sharedWorkspace] frontmostApplication];
        if (frontmost && frontmost.localizedName) {
            std::string appName = std::string([frontmost.localizedName UTF8String]);
            LogToTerminusDB(appName);
        }
        
        // Run loop blocks indefinitely and consumes near 0 CPU until an event fires
        [[NSRunLoop currentRunLoop] run];
    }
    return 0;
}
