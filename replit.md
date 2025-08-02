# MediFly Hospital MVP

## Overview

MediFly is a Flask-based web application that simulates a hospital interface for booking air medical transport services. The system provides a streamlined workflow for hospital staff to coordinate critical patient transports, from initial intake through flight tracking and completion. The application features a multi-step guided form, provider comparison, booking confirmation, real-time flight tracking simulation, and administrative oversight capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with a base template system for consistent layout
- **UI Framework**: Bootstrap 5 for responsive design and component styling
- **JavaScript Enhancement**: Custom JavaScript for form navigation, validation, and interactive features
- **Chatbot Integration**: BotUI library integration for conversational interfaces
- **Accessibility**: ARIA labels and semantic HTML for screen reader compatibility

### Backend Architecture
- **Web Framework**: Flask with session-based state management
- **Route Structure**: RESTful routes following a logical user journey (intake → results → confirm → tracking → summary)
- **Data Storage**: Session-based temporary storage with no persistent database
- **Mock Data System**: In-memory provider data simulation for demonstration purposes
- **Logging**: Python logging module for debugging and monitoring

### State Management
- **Session Storage**: Flask sessions for maintaining user data throughout the booking process
- **Temporary Data**: In-memory dictionaries for provider information and tracking stages
- **Security**: Session secret key configuration through environment variables
- **Data Flow**: Linear progression through booking stages with form validation

### Authentication System
- **Admin Access**: Simple credential-based authentication for administrative functions
- **Session Management**: Flask session handling for admin authentication state
- **Security Model**: Basic username/password authentication with demo credentials

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: CSS framework via CDN for responsive design and components
- **Font Awesome 6**: Icon library via CDN for consistent iconography
- **BotUI**: Chatbot interface library for conversational form interactions

### Backend Dependencies
- **Flask**: Core web framework for routing and request handling
- **Python Standard Library**: datetime, os, logging modules for core functionality

### Environment Configuration
- **SESSION_SECRET**: Environment variable for Flask session security
- **Development Server**: Flask development server with debug mode enabled

### Third-party Integrations
- **CDN Services**: Bootstrap, Font Awesome, and BotUI served via content delivery networks
- **No Database**: Intentionally database-free design for simplicity and demonstration purposes
- **No Email Service**: Mock email notifications logged to console for demonstration