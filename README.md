# MoldCraft - Silicone Molds E-commerce Website

A modern e-commerce website for selling silicone molds for soap and chocolate making. Built with Python Flask, featuring beautiful animations and a responsive design.

## Features

- Modern, responsive design with beautiful gradients and animations
- User authentication system
- Product catalog with detailed views
- Shopping cart functionality
- Contact form
- Mobile-friendly interface

## Prerequisites

- Python 3.8 or higher
- pip3 (Python package manager)
- A modern web browser
- C++ compiler (for the configuration script)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moldcraft.git
cd moldcraft
```

2. Compile and run the configuration script:
```bash
# On Windows:
g++ configure.cpp -o configure
.\configure

# On Linux/macOS:
g++ configure.cpp -o configure
./configure
```

3. Activate the virtual environment:
```bash
# On Windows:
.\venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

4. Start the development server:
```bash
python3 app.py
```

5. Visit `http://localhost:5000` in your web browser

## Troubleshooting

### Common Issues

1. **Python3 not found**
   - Make sure Python3 is installed:
     ```bash
     # On Ubuntu/Debian:
     sudo apt-get install python3 python3-venv python3-pip
     
     # On macOS:
     brew install python3
     
     # On Windows:
     # Download and install from python.org
     ```
   - Verify installation:
     ```bash
     python3 --version
     ```

2. **Virtual environment issues**
   - If the virtual environment creation fails, try installing `python3-venv`:
     ```bash
     # On Ubuntu/Debian:
     sudo apt-get install python3-venv
     
     # On macOS:
     brew install python3
     ```

3. **Database initialization errors**
   - Make sure you're in the virtual environment when running the server
   - Check if the `store.db` file has proper write permissions
   - Try removing the existing database and letting it recreate:
     ```bash
     rm store.db
     python3 -c "from app import db; db.create_all()"
     ```

## Project Structure

```
moldcraft/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── configure.cpp       # Configuration script
├── venv/              # Python virtual environment
├── static/
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── images/        # Image assets
└── templates/         # HTML templates
```

## Technologies Used

- Backend:
  - Python 3
  - Flask
  - SQLAlchemy
  - Flask-Login

- Frontend:
  - HTML5
  - CSS3 (with modern features like CSS Grid and Flexbox)
  - JavaScript (ES6+)
  - Font Awesome icons

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Your Name - your.email@example.com
Project Link: https://github.com/yourusername/moldcraft 