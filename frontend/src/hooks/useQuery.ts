// frontend/src/hooks/useQuery.ts
//
// Custom hook for data fetching with loading and error states.
//
// Educational Notes for Junior Developers:
// - Custom hooks: Encapsulate stateful logic that can be reused across components.
// - Error boundaries: Consider how to handle errors at the UI level.
// - Loading states: Different loading indicators for initial vs. refresh.
// - Cache strategy: Simple in-memory cache for frequently accessed data.

import { useState, useEffect } from 'react'

interface QueryState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

// Simple in-memory cache
// Educational Note: Production apps would use more sophisticated caching
// (React Query, SWR, or Redux Toolkit Query for cache management, invalidation, etc.)
const cache = new Map<string, any>()

export function useQuery<T>(
  queryFn: () => Promise<T>,
  cacheKey?: string
): QueryState<T> {
  const [state, setState] = useState<QueryState<T>>({
    data: null,
    loading: true,
    error: null
  })

  useEffect(() => {
    let isMounted = true

    async function fetchData() {
      setState(prev => ({ ...prev, loading: true, error: null }))

      // Check cache first
      // Why cache: Avoid unnecessary API calls for same data
      if (cacheKey && cache.has(cacheKey)) {
        const cachedData = cache.get(cacheKey)
        if (isMounted) {
          setState({ data: cachedData, loading: false, error: null })
        }
        return
      }

      try {
        const data = await queryFn()

        // Cache the result
        // Tradeoff: Memory usage vs. performance improvement
        if (cacheKey) {
          cache.set(cacheKey, data)
        }

        if (isMounted) {
          setState({ data, loading: false, error: null })
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'An error occurred'

        if (isMounted) {
          setState({
            data: null,
            loading: false,
            error: errorMessage
          })
        }
      }
    }

    fetchData()

    // Cleanup function to prevent state updates on unmounted components
    // Why: Prevent memory leaks and potential runtime errors
    return () => {
      isMounted = false
    }
  }, [cacheKey, queryFn])

  return state
}

// Utility function to clear cache
// Useful when data is updated and cache needs invalidation
export function clearCache(keys?: string[]) {
  if (keys) {
    keys.forEach(key => cache.delete(key))
  } else {
    cache.clear()
  }
}
