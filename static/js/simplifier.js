/**
 * Technical Term Simplifier
 * 
 * This script allows users to select any text for explanation
 * and also automatically highlights common technical terms.
 */

class TechnicalTermSimplifier {
    constructor(options = {}) {
        // Configuration
        this.options = {
            apiEndpoint: options.apiEndpoint || '/simplifier/explain',
            highlightEndpoint: options.highlightEndpoint || '/simplifier/identify-terms',
            tooltipClass: options.tooltipClass || 'term-simplifier-tooltip',
            highlightClass: options.highlightClass || 'technical-term-highlight',
            containerSelector: options.containerSelector || 'body',
            contentSelector: options.contentSelector || '.content-area',
            tooltipDelay: options.tooltipDelay || 300,
            tooltipHideDelay: options.tooltipHideDelay || 2000,
            maxSelectionLength: options.maxSelectionLength || 50,
            tooltipOffset: options.tooltipOffset || 10,
            preferredPosition: options.preferredPosition || 'above',
            autoHighlight: options.autoHighlight !== false,
            minTermLength: options.minTermLength || 3
        };

        // State
        this.explainedTerms = new Map();  // Cache for explanations
        this.pendingExplanations = new Map(); // Track in-progress requests by term
        this.knownTechnicalTerms = new Set(); // Set of known technical terms
        this.activeTooltip = null;
        this.tooltipHideTimeout = null;
        this.selectionTimeout = null;
        this.currentTerm = null;  // Currently displayed term
        
        // Initialize
        this.initialize();
    }

    async initialize() {
        console.log('Initializing Technical Term Simplifier (Dual Mode)...');
        
        // Create tooltip element
        this.createTooltipElement();
        
        // Add selection event listeners
        this.setupSelectionListeners();
        
        // Get common technical terms and highlight them
        if (this.options.autoHighlight) {
            await this.loadTechnicalTerms();
            this.highlightTechnicalTerms();
        }
        
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
            tooltip.style.position = 'fixed';
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
        
        // Track current hovered term element
        this.currentHoveredElement = null;
        
        // Add mouseover event for highlighted terms
        document.addEventListener('mouseover', (event) => {
            // Check if the target is a highlighted term
            const target = event.target;
            
            if (target && target.classList && 
                target.classList.contains(this.options.highlightClass)) {
                
                // Update currently hovered element
                this.currentHoveredElement = target;
                
                // Handle the hover
                this.handleTermHover(target);
            }
        });
        
        // Hide tooltip when mouse leaves highlighted term
        document.addEventListener('mouseout', (event) => {
            const target = event.target;
            
            // Only hide if we're leaving a highlighted term and not entering the tooltip
            if (target && target.classList && 
                target.classList.contains(this.options.highlightClass)) {
                
                // Check if we're moving to the tooltip
                const relatedTarget = event.relatedTarget;
                if (relatedTarget && 
                    (relatedTarget === this.tooltipElement || 
                     this.tooltipElement.contains(relatedTarget))) {
                    return; // Moving to tooltip, don't hide
                }
                
                // Clear current hovered element
                if (this.currentHoveredElement === target) {
                    this.currentHoveredElement = null;
                }
                
                // Don't hide immediately - use a small delay
                // This gives the user time to move to the tooltip if desired
                setTimeout(() => {
                    // Only hide if we haven't hovered another term
                    if (!this.currentHoveredElement) {
                        this.hideTooltip();
                    }
                }, 300);
            }
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
            
            // Set current term
            this.currentTerm = selectedText;
            
            // Show loading state
            this.showTooltip(`Getting explanation for "${selectedText}"...`);
            
            // First check cache
            let explanation = this.explainedTerms.get(selectedText.toLowerCase());
            
            if (!explanation) {
                explanation = await this.getExplanationWithUpdate(selectedText);
            } else {
                this.showTooltip(`<strong>${selectedText}</strong>: ${explanation}`);
            }
        } catch (error) {
            console.error('Error handling selection:', error);
            this.hideTooltip();
        }
    }

    async handleTermHover(termElement) {
        const term = termElement.textContent.trim();
        
        // Don't do anything if this is the same term we're already showing
        if (term === this.currentTerm && this.tooltipElement.style.display !== 'none') {
            return;
        }
        
        // Get element position
        const rect = termElement.getBoundingClientRect();
        this.activeSelectionRect = rect;
        
        // Update current term
        this.currentTerm = term;
        
        // Check for cached explanation
        let explanation = this.explainedTerms.get(term.toLowerCase());
        
        if (explanation) {
            // Show cached explanation immediately
            this.showTooltip(`<strong>${term}</strong>: ${explanation}`);
        } else {
            // Check if we have a pending request
            const pendingPromise = this.pendingExplanations.get(term.toLowerCase());
            
            if (pendingPromise) {
                // Show loading and wait for the existing request
                this.showTooltip(`Getting explanation for "${term}"...`);
                
                try {
                    explanation = await pendingPromise;
                    
                    // Only update if this is still the current term
                    if (term === this.currentTerm) {
                        this.showTooltip(`<strong>${term}</strong>: ${explanation}`);
                    }
                } catch (error) {
                    console.error('Error waiting for pending explanation:', error);
                }
            } else {
                // No pending request - start a new one
                this.showTooltip(`Getting explanation for "${term}"...`);
                await this.getExplanationWithUpdate(term);
            }
        }
    }
    

async getExplanationWithUpdate(term) {
    try {
        // Show loading state immediately
        if (term === this.currentTerm) {
            this.showTooltip(`Getting explanation for "${term}"...`);
        }
        
        // Create a promise that will get resolved when the explanation is ready
        const explanationPromise = this.fetchExplanation(term);
        
        // Store the promise in pendingExplanations
        this.pendingExplanations.set(term.toLowerCase(), explanationPromise);
        
        try {
            // Wait for the explanation
            const explanation = await explanationPromise;
            
            // Only update if this is still the current term
            if (term === this.currentTerm) {
                this.showTooltip(`<strong>${term}</strong>: ${explanation}`);
            }
            
            // Remove from pending
            this.pendingExplanations.delete(term.toLowerCase());
            
            return explanation;
            
        } catch (error) {
            // Remove from pending since the request failed
            this.pendingExplanations.delete(term.toLowerCase());
            
            console.error(`Error getting explanation for ${term}:`, error);
            
            // Only update the error message if this is still the current term
            if (term === this.currentTerm) {
                this.showTooltip(`<strong>${term}</strong>: This term cannot be explained right now.`);
            }
            
            // Return a default message that won't be cached
            return `This term cannot be explained right now.`;
        }
    } catch (error) {
        console.error(`Outer error in getExplanationWithUpdate for ${term}:`, error);
        
        // Only update UI if this is still the current term
        if (term === this.currentTerm) {
            this.showTooltip(`<strong>${term}</strong>: Sorry, could not get an explanation.`);
        }
        
        return 'Sorry, could not get an explanation for this term.';
    }
}

    async loadTechnicalTerms() {
        try {
            // Either fetch from API or use a built-in list
            // You can adapt this to use a local list or fetch from your backend
            
            // Option 1: Use built-in list (faster)
            this.addCommonTechnicalTerms();
            
            // Option 2: Fetch from API
            /* 
            const response = await fetch(this.options.highlightEndpoint);
            if (response.ok) {
                const data = await response.json();
                if (data.terms && Array.isArray(data.terms)) {
                    data.terms.forEach(term => {
                        this.knownTechnicalTerms.add(term.toLowerCase());
                    });
                }
            }
            */
            
            console.log(`Loaded ${this.knownTechnicalTerms.size} technical terms for highlighting`);
            
        } catch (error) {
            console.error('Error loading technical terms:', error);
        }
    }

    addCommonTechnicalTerms() {
        // Common technical terms to highlight
        const commonTerms = [
            "api", "rest", "json", "http", "url", "html", "css", "javascript",
            "python", "database", "sql", "server", "client", "backend", "frontend",
            "framework", "library", "function", "variable", "algorithm", "data structure",
            "cloud", "hosting", "deployment", "container", "docker", "kubernetes",
            "microservice", "authentication", "authorization", "encryption", "api key",
            "endpoint", "git", "repository", "commit", "branch", "merge", "pull request",
            "compiler", "interpreter", "runtime", "debugging", "testing", "unit test",
            "integration", "agile", "scrum", "waterfall", "sprint", "backlog", 
            "bandwidth", "latency", "cache", "memory", "cpu", "gpu", "thread", "process",
            "asynchronous", "synchronous", "concurrency", "ajax", "xml", "yaml", "markdown",
            "regex", "expression", "npm", "yarn", "webpack", "babel", "typescript",
            "react", "angular", "vue", "node", "express", "django", "flask", "ruby",
            "rails", "php", "laravel", "java", "spring", "hibernate", "orm",
            "nosql", "mongodb", "redis", "postgresql", "mysql", "aws", "azure", "gcp",
            "devops", "cicd", "jenkins", "travis", "github", "gitlab", "bitbucket"
        ];
        
        commonTerms.forEach(term => {
            this.knownTechnicalTerms.add(term.toLowerCase());
        });
    }

    highlightTechnicalTerms() {
        // Select content area(s) to process
        const contentAreas = document.querySelectorAll(this.options.contentSelector);
        
        if (!contentAreas.length) {
            console.log('No content areas found for highlighting');
            return;
        }
        
        console.log(`Found ${contentAreas.length} content areas for highlighting`);
        
        contentAreas.forEach(contentArea => {
            this.processNode(contentArea);
        });
    }

    processNode(node) {
        // Skip script and style elements
        if (node.nodeName === 'SCRIPT' || node.nodeName === 'STYLE') {
            return;
        }
        
        // Process text nodes
        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
            this.highlightTermsInTextNode(node);
            return;
        }
        
        // Skip already processed nodes or nodes with the highlight class
        if (node.classList && 
            (node.classList.contains('processed-for-highlight') || 
             node.classList.contains(this.options.highlightClass))) {
            return;
        }
        
        // Process children recursively
        const childNodes = Array.from(node.childNodes);
        childNodes.forEach(childNode => {
            this.processNode(childNode);
        });
        
        // Mark as processed
        if (node.classList) {
            node.classList.add('processed-for-highlight');
        }
    }

    highlightTermsInTextNode(textNode) {
        const text = textNode.textContent;
        
        // No need to process very short text
        if (text.length < this.options.minTermLength) {
            return;
        }
        
        // Create a temporary element to hold the new content
        const tempElement = document.createElement('span');
        
        // Split text into words and punctuation
        // This regex keeps punctuation separate from words
        const parts = text.split(/(\W+)/);
        
        // Process each part
        let hasHighlights = false;
        let newHtml = '';
        
        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (/\w+/.test(part)) { // If this part contains word characters
                // Check if it's a technical term
                if (part.length >= this.options.minTermLength && 
                    this.knownTechnicalTerms.has(part.toLowerCase())) {
                    // It's a technical term, highlight it
                    newHtml += `<span class="${this.options.highlightClass}">${part}</span>`;
                    hasHighlights = true;
                } else {
                    // Regular word
                    newHtml += part;
                }
            } else {
                // Punctuation or whitespace, keep as is
                newHtml += part;
            }
        }
        
        // If we found and highlighted any terms, replace the text node
        if (hasHighlights) {
            tempElement.innerHTML = newHtml;
            
            // Replace the text node with our new elements
            const parent = textNode.parentNode;
            const fragment = document.createDocumentFragment();
            
            while (tempElement.firstChild) {
                fragment.appendChild(tempElement.firstChild);
            }
            
            parent.replaceChild(fragment, textNode);
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
        
        // Check if we got a valid explanation
        const explanation = data.explanation;
        
        if (!explanation || 
            explanation === "Sorry, I couldn't explain that term right now." ||
            explanation.includes("couldn't explain")) {
            
            console.warn(`Received invalid explanation for '${term}': "${explanation}"`);
            throw new Error('Invalid explanation received from server');
        }
        
        // Add valid explanation to cache
        this.explainedTerms.set(term.toLowerCase(), explanation);
        
        return explanation;
        
    } catch (error) {
        console.error('Error fetching explanation:', error);
        
        // Let the caller handle the error
        throw error;
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
            this.currentTerm = null; // Clear current term
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.technicalTermSimplifier = new TechnicalTermSimplifier({
        apiEndpoint: '/simplifier/explain',
        containerSelector: 'body',
        contentSelector: '.content-area, article, p, div.main-content',
        preferredPosition: 'above',
        autoHighlight: true
    });
});