import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface EnhancedPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
  className?: string;
}

const EnhancedPagination: React.FC<EnhancedPaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  isLoading = false,
  className
}) => {
  // Don't render if there's only one page
  if (totalPages <= 1) return null;

  const handlePageChange = (page: number) => {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };

  // Generate page numbers with smart ellipsis
  const generatePageNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisiblePages = 7; // Show more pages for better UX
    
    if (totalPages <= maxVisiblePages) {
      // If total pages is small, show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Smart pagination with ellipsis
      const leftBound = Math.max(1, currentPage - 2);
      const rightBound = Math.min(totalPages, currentPage + 2);
      
      // Always show first page
      pages.push(1);
      
      // Add ellipsis if there's a gap
      if (leftBound > 2) {
        pages.push('ellipsis');
      }
      
      // Add pages around current page
      for (let i = Math.max(2, leftBound); i <= Math.min(totalPages - 1, rightBound); i++) {
        pages.push(i);
      }
      
      // Add ellipsis if there's a gap
      if (rightBound < totalPages - 1) {
        pages.push('ellipsis');
      }
      
      // Always show last page
      if (totalPages > 1) {
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  const pageNumbers = generatePageNumbers();

  return (
    <div className={cn("flex flex-col items-center space-y-4", className)}>
      {/* Results Info */}
      <div className="text-center">
        <p className="text-sm text-gray-700">
          Page <span className="font-semibold text-gray-900">{currentPage}</span> of{' '}
          <span className="font-semibold text-gray-900">{totalPages}</span>
        </p>
      </div>

      {/* Desktop Pagination Controls */}
      <div className="hidden md:flex items-center gap-2">
        {/* First Page Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(1)}
          disabled={currentPage === 1 || isLoading}
          className={cn(
            "px-3 py-2 h-10 min-w-[44px] transition-all duration-200",
            currentPage === 1 
              ? "opacity-50 cursor-not-allowed" 
              : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
          )}
          aria-label="Go to first page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>

        {/* Previous Page Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1 || isLoading}
          className={cn(
            "px-3 py-2 h-10 min-w-[44px] transition-all duration-200",
            currentPage === 1 
              ? "opacity-50 cursor-not-allowed" 
              : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
          )}
          aria-label="Go to previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {/* Page Numbers */}
        <div className="flex items-center gap-1">
          {pageNumbers.map((page, index) => (
            <React.Fragment key={index}>
              {page === 'ellipsis' ? (
                <span className="flex h-10 w-10 items-center justify-center text-gray-500 select-none">
                  <span className="text-lg">⋯</span>
                </span>
              ) : (
                <Button
                  variant={currentPage === page ? "default" : "outline"}
                  size="sm"
                  onClick={() => handlePageChange(page)}
                  disabled={isLoading}
                  className={cn(
                    "h-10 min-w-[44px] text-base font-medium transition-all duration-200",
                    currentPage === page 
                      ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md ring-2 ring-blue-200" 
                      : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  )}
                  aria-label={`Go to page ${page}`}
                  aria-current={currentPage === page ? 'page' : undefined}
                >
                  {page}
                </Button>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Next Page Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages || isLoading}
          className={cn(
            "px-3 py-2 h-10 min-w-[44px] transition-all duration-200",
            currentPage === totalPages 
              ? "opacity-50 cursor-not-allowed" 
              : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
          )}
          aria-label="Go to next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>

        {/* Last Page Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(totalPages)}
          disabled={currentPage === totalPages || isLoading}
          className={cn(
            "px-3 py-2 h-10 min-w-[44px] transition-all duration-200",
            currentPage === totalPages 
              ? "opacity-50 cursor-not-allowed" 
              : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
          )}
          aria-label="Go to last page"
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Mobile Pagination Controls - Touch Friendly */}
      <div className="md:hidden flex flex-col items-center space-y-3 w-full">
        {/* Mobile Page Numbers - Larger touch targets */}
        <div className="flex items-center gap-2 flex-wrap justify-center">
          {pageNumbers.map((page, index) => (
            <React.Fragment key={index}>
              {page === 'ellipsis' ? (
                <span className="flex h-12 w-12 items-center justify-center text-gray-500 select-none">
                  <span className="text-xl">⋯</span>
                </span>
              ) : (
                <Button
                  variant={currentPage === page ? "default" : "outline"}
                  size="default"
                  onClick={() => handlePageChange(page)}
                  disabled={isLoading}
                  className={cn(
                    "h-12 min-w-[48px] text-lg font-medium transition-all duration-200",
                    currentPage === page 
                      ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md ring-2 ring-blue-200" 
                      : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  )}
                  aria-label={`Go to page ${page}`}
                  aria-current={currentPage === page ? 'page' : undefined}
                >
                  {page}
                </Button>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Mobile Navigation Buttons - Full Width */}
        <div className="flex items-center gap-3 w-full max-w-xs">
          <Button
            variant="outline"
            size="default"
            onClick={() => handlePageChange(1)}
            disabled={currentPage === 1 || isLoading}
            className={cn(
              "flex-1 h-12 text-sm font-medium transition-all duration-200",
              currentPage === 1 
                ? "opacity-50 cursor-not-allowed" 
                : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
            )}
            aria-label="Go to first page"
          >
            <ChevronsLeft className="h-5 w-5 mr-1" />
            First
          </Button>

          <Button
            variant="outline"
            size="default"
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1 || isLoading}
            className={cn(
              "flex-1 h-12 text-sm font-medium transition-all duration-200",
              currentPage === 1 
                ? "opacity-50 cursor-not-allowed" 
                : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
            )}
            aria-label="Go to previous page"
          >
            <ChevronLeft className="h-5 w-5 mr-1" />
            Prev
          </Button>

          <Button
            variant="outline"
            size="default"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages || isLoading}
            className={cn(
              "flex-1 h-12 text-sm font-medium transition-all duration-200",
              currentPage === totalPages 
                ? "opacity-50 cursor-not-allowed" 
                : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
            )}
            aria-label="Go to next page"
          >
            Next
            <ChevronRight className="h-5 w-5 ml-1" />
          </Button>

          <Button
            variant="outline"
            size="default"
            onClick={() => handlePageChange(totalPages)}
            disabled={currentPage === totalPages || isLoading}
            className={cn(
              "flex-1 h-12 text-sm font-medium transition-all duration-200",
              currentPage === totalPages 
                ? "opacity-50 cursor-not-allowed" 
                : "hover:bg-gray-50 hover:border-gray-300 hover:shadow-sm"
            )}
            aria-label="Go to last page"
          >
            Last
            <ChevronsRight className="h-5 w-5 ml-1" />
          </Button>
        </div>
      </div>

      {/* Quick Jump (Optional - for very long page lists) */}
      {totalPages > 20 && (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Go to page:</span>
          <input
            type="number"
            min="1"
            max={totalPages}
            value=""
            onChange={(e) => {
              const page = parseInt(e.target.value);
              if (page >= 1 && page <= totalPages) {
                handlePageChange(page);
                e.target.value = '';
              }
            }}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                const page = parseInt(e.currentTarget.value);
                if (page >= 1 && page <= totalPages) {
                  handlePageChange(page);
                  e.currentTarget.value = '';
                }
              }
            }}
            className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            placeholder="Page #"
          />
        </div>
      )}
    </div>
  );
};

export default EnhancedPagination; 