#include <iostream>
#include <cstdlib>
#include <string>
#include <filesystem>

namespace fs = std::filesystem;

bool executeCommand(const std::string& command) {
    int result = system(command.c_str());
    return result == 0;
}

int main() {
    std::cout << "Setting up MoldCraft website...\n\n";
    
    // Create virtual environment
    std::cout << "Creating Python virtual environment...\n";
    if (!executeCommand("python3 -m venv venv")) {
        std::cout << "Error: Failed to create virtual environment\n";
        return 1;
    }
    
    // Install Python dependencies
    std::cout << "Installing Python dependencies...\n";
    #ifdef _WIN32
        if (!executeCommand(".\\venv\\Scripts\\pip3 install -r requirements.txt")) {
            std::cout << "Error: Failed to install Python dependencies\n";
            return 1;
        }
    #else
        // On Unix-like systems, use the full path to pip
        if (!executeCommand("./venv/bin/pip3 install -r requirements.txt")) {
            std::cout << "Error: Failed to install Python dependencies\n";
            return 1;
        }
    #endif
    
    // Create necessary directories
    std::cout << "\nCreating project directories...\n";
    try {
        fs::create_directories("static/css");
        fs::create_directories("static/js");
        fs::create_directories("static/images");
        fs::create_directories("templates");
    } catch (const std::exception& e) {
        std::cout << "Error creating directories: " << e.what() << "\n";
        return 1;
    }
    
    // Initialize database
    std::cout << "\nInitializing database...\n";
    #ifdef _WIN32
        if (!executeCommand(".\\venv\\Scripts\\python3 -c \"from app import db; db.create_all()\"")) {
            std::cout << "Error: Failed to initialize database\n";
            return 1;
        }
    #else
        if (!executeCommand("./venv/bin/python3 -c \"from app import db; db.create_all()\"")) {
            std::cout << "Error: Failed to initialize database\n";
            return 1;
        }
    #endif
    
    std::cout << "\nInstallation complete! To run the website:\n";
    #ifdef _WIN32
        std::cout << "1. Activate the virtual environment: .\\venv\\Scripts\\activate\n";
        std::cout << "2. Run the server: python3 app.py\n";
    #else
        std::cout << "1. Activate the virtual environment: source venv/bin/activate\n";
        std::cout << "2. Run the server: python3 app.py\n";
    #endif
    
    return 0;
} 