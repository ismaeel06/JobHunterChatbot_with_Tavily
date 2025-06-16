/**
 * Technical Term Simplifier
 * 
 * This script allows users to select any text and get a simple explanation.
 */

class TechnicalTermSimplifier {
    constructor(options = {}) {
        // Configuration
        this.options = {
            apiEndpoint: options.apiEndpoint || '/simplifier/explain',
            tooltipClass: options.tooltipClass || 'term-simplifier-tooltip',
            containerSelector: options.containerSelector || 'body',
            tooltipDelay: options.tooltipDelay || 300,
            tooltipHideDelay: options.tooltipHideDelay || 2000,
            maxSelectionLength: options.maxSelectionLength || 50,
            tooltipOffset: options.tooltipOffset || 10,  // Distance from selection
            preferredPosition: options.preferredPosition || 'above'  // 'above' or 'below'
        };

        // State
        this.explainedTerms = new Map();  // Cache for explanations
        this.activeTooltip = null;
        this.tooltipHideTimeout = null;
        this.selectionTimeout = null;
        
        // Initialize
        this.initialize();
    }

    initialize() {
        console.log('Initializing Technical Term Simplifier (Selection Mode)...');
        
        // Create tooltip element
        this.createTooltipElement();
        
        // Add selection event listeners
        this.setupSelectionListeners();
        
        console.log('Technical Term Simplifier initialized');
    }

    createTooltipElement() {
        // Create tooltip if it doesn't exist
        let tooltip = document.getElementById(this.options.tooltipClass);
        
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = this.options.tooltipClass;
            tooltip.className = this.options.tooltipClass;
            tooltip.style.display = 'none';
            tooltip.style.position = 'fixed'; // Use fixed positioning for viewport-relative positioning
            tooltip.style.zIndex = '9999';
            
            document.body.appendChild(tooltip);
        }
        
        this.tooltipElement = tooltip;
    }

    setupSelectionListeners() {
        // Listen for text selections within the container
        const container = document.querySelector(this.options.containerSelector);
        if (!container) {
            console.error('Container not found:', this.options.containerSelector);
            return;
        }
        
        // Add mouseup event to detect selections
        document.addEventListener('mouseup', (event) => {
            clearTimeout(this.selectionTimeout);
            
            // Add a small delay to allow the selection to complete
            this.selectionTimeout = setTimeout(() => {
                this.handleSelection(event);
            }, 200);
        });
        
        // Hide tooltip when clicking elsewhere
        document.addEventListener('mousedown', (event) => {
            if (this.tooltipElement && 
                event.target !== this.tooltipElement && 
                !this.tooltipElement.contains(event.target)) {
                this.hideTooltip();
            }
        });
        
        // Reposition tooltip on scroll and resize
        window.addEventListener('scroll', () => {
            if (this.tooltipElement && this.tooltipElement.style.display !== 'none') {
                // If tooltip is visible and we have active selection, reposition it
                if (this.activeSelectionRect) {
                    this.positionTooltip(this.activeSelectionRect);
                } else {
                    this.hideTooltip();
                }
            }
        }, { passive: true });
        
        window.addEventListener('resize', () => {
            if (this.tooltipElement && this.tooltipElement.style.display !== 'none') {
                if (this.activeSelectionRect) {
                    this.positionTooltip(this.activeSelectionRect);
                } else {
                    this.hideTooltip();
                }
            }
        });
    }

    async handleSelection(event) {
        const selection = window.getSelection();
        
        if (!selection || selection.isCollapsed) {
            return;
        }
        
        const selectedText = selection.toString().trim();
        
        // Ignore empty or very long selections
        if (!selectedText || 
            selectedText.length < 2 || 
            selectedText.length > this.options.maxSelectionLength) {
            return;
        }
        
        // Check if the selection is a word or short phrase (rough check)
        if (selectedText.split(/\s+/).length > 3) {
            console.log('Selection too long, not explaining');
            return;
        }
        
        try {
            // Get selection position - crucial for correct positioning
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            // Save this rect for repositioning if needed
            this.activeSelectionRect = rect;
            
            // Show loading state
            this.showTooltip(`Getting explanation for "${selectedText}"...`);
            
            // First check cache
            let explanation = this.explainedTerms.get(selectedText.toLowerCase());
            
            if (!explanation) {
                explanation = await this.fetchExplanation(selectedText);
                
                if (explanation) {
                    this.explainedTerms.set(selectedText.toLowerCase(), explanation);
                }
            }
            
            if (explanation) {
                this.showTooltip(`<strong>${selectedText}</strong>: ${explanation}`);
            }
        } catch (error) {
            console.error('Error handling selection:', error);
            this.hideTooltip();
        }
    }

    async fetchExplanation(term) {
        try {
            console.log(`Fetching explanation for: ${term}`);
            
            const response = await fetch(this.options.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ term })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to fetch explanation: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Explanation data received:', data);
            
            return data.explanation;
            
        } catch (error) {
            console.error('Error fetching explanation:', error);
            return 'Sorry, could not get an explanation for this term. Try again later.';
        }
    }

    showTooltip(content) {
        clearTimeout(this.tooltipHideTimeout);
        
        // Update content
        this.tooltipElement.innerHTML = content;
        this.tooltipElement.style.display = 'block';
        
        // Position the tooltip correctly
        if (this.activeSelectionRect) {
            this.positionTooltip(this.activeSelectionRect);
        }
        
        // Auto-hide tooltip after a delay
        this.tooltipHideTimeout = setTimeout(() => {
            this.hideTooltip();
        }, 10000); // 10 seconds before auto-hiding
    }
    
    positionTooltip(rect) {
        // This is the crucial method for correct positioning
        // rect is viewport-relative (from getBoundingClientRect)
        
        const tooltipHeight = this.tooltipElement.offsetHeight;
        const tooltipWidth = this.tooltipElement.offsetWidth;
        const offset = this.options.tooltipOffset;
        
        let top, left;
        
        // Decide if tooltip should be above or below selection
        const viewportHeight = window.innerHeight;
        const spaceAbove = rect.top;
        const spaceBelow = viewportHeight - rect.bottom;
        
        // Place above by default or if specified, unless there's not enough space
        const placeAbove = (this.options.preferredPosition === 'above' && spaceAbove >= tooltipHeight + offset) || 
                           (spaceBelow < tooltipHeight + offset && spaceAbove >= tooltipHeight + offset);
        
        if (placeAbove) {
            // Position above the selection
            top = rect.top - tooltipHeight - offset;
        } else {
            // Position below the selection
            top = rect.bottom + offset;
        }
        
        // Center horizontally over the selection
        left = rect.left + (rect.width / 2) - (tooltipWidth / 2);
        
        // Ensure tooltip is within viewport horizontally
        if (left < 10) left = 10;
        if (left + tooltipWidth > window.innerWidth - 10) {
            left = window.innerWidth - tooltipWidth - 10;
        }
        
        // Apply the position - using fixed positioning relative to viewport
        this.tooltipElement.style.top = `${top}px`;
        this.tooltipElement.style.left = `${left}px`;
        
        // Add a visual indicator of positioning
        this.tooltipElement.classList.remove('position-above', 'position-below');
        this.tooltipElement.classList.add(placeAbove ? 'position-above' : 'position-below');
    }

    hideTooltip() {
        if (this.tooltipElement) {
            this.tooltipElement.style.display = 'none';
            this.activeSelectionRect = null; // Clear active selection
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.technicalTermSimplifier = new TechnicalTermSimplifier({
        apiEndpoint: '/simplifier/explain',
        containerSelector: 'body',
        preferredPosition: 'above'  // 'above' or 'below'
    });
});