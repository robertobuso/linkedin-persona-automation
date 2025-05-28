window.APP_CONFIG = {
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000/api/v1'
        : '/api/v1',
    
    APP_NAME: 'LinkedIn Automation MVP',
    VERSION: '1.0.0',
    
    // Feature flags
    FEATURES: {
        BATCH_GENERATION: true,
        DRAFT_EDITING: true,
        CONTENT_FILTERING: true,
        ANALYTICS: false  // Disabled for MVP
    },
    
    // UI Configuration
    PAGINATION: {
        DEFAULT_PAGE_SIZE: 20,
        MAX_PAGE_SIZE: 100
    },
    
    // Content limits
    LIMITS: {
        MAX_CONTENT_SOURCES: 10,
        MAX_DRAFTS_PER_BATCH: 5,
        CONTENT_PREVIEW_LENGTH: 200
    }
};