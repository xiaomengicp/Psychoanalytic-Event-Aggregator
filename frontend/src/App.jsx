import { useState, useEffect, useMemo } from 'react'
import { useEvents } from './hooks/useEvents'
import FilterBar from './components/FilterBar'
import EventList from './components/EventList'

// Data URL - update this after deployment
const DATA_URL = './data/events.json'

function App() {
    const { events, loading, error, lastUpdated } = useEvents(DATA_URL)
    const [filters, setFilters] = useState({
        search: '',
        format: [],
        eventType: [],
        startDate: '',
        endDate: '',
        organization: '',
    })
    const [sortBy, setSortBy] = useState('date')

    // Get unique organizations for filter dropdown
    const organizations = useMemo(() => {
        const orgs = new Set(events.map(e => e.organizer?.name).filter(Boolean))
        return Array.from(orgs).sort()
    }, [events])

    // Filter and sort events
    const filteredEvents = useMemo(() => {
        let result = [...events]

        // Text search
        if (filters.search) {
            const searchLower = filters.search.toLowerCase()
            result = result.filter(e =>
                e.title?.toLowerCase().includes(searchLower) ||
                e.description?.toLowerCase().includes(searchLower) ||
                e.organizer?.name?.toLowerCase().includes(searchLower)
            )
        }

        // Format filter
        if (filters.format.length > 0) {
            result = result.filter(e => filters.format.includes(e.format))
        }

        // Event type filter
        if (filters.eventType.length > 0) {
            result = result.filter(e => filters.eventType.includes(e.event_type))
        }

        // Organization filter
        if (filters.organization) {
            result = result.filter(e => e.organizer?.name === filters.organization)
        }

        // Date range
        if (filters.startDate) {
            const start = new Date(filters.startDate)
            result = result.filter(e => e.start_date && new Date(e.start_date) >= start)
        }
        if (filters.endDate) {
            const end = new Date(filters.endDate)
            result = result.filter(e => e.start_date && new Date(e.start_date) <= end)
        }

        // Sort
        result.sort((a, b) => {
            switch (sortBy) {
                case 'date':
                    const dateA = a.start_date ? new Date(a.start_date) : new Date(9999, 11, 31)
                    const dateB = b.start_date ? new Date(b.start_date) : new Date(9999, 11, 31)
                    return dateA - dateB
                case 'title':
                    return (a.title || '').localeCompare(b.title || '')
                case 'completeness':
                    return (b.completeness_score || 0) - (a.completeness_score || 0)
                default:
                    return 0
            }
        })

        return result
    }, [events, filters, sortBy])

    return (
        <div className="min-h-screen">
            {/* Header */}
            <header className="glass-card sticky top-0 z-50 border-b border-purple-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                                <span className="text-white text-xl font-serif">ψ</span>
                            </div>
                            <div>
                                <h1 className="text-xl font-display font-bold gradient-text">
                                    Psychoanalytic Events
                                </h1>
                                <p className="text-xs text-gray-500">
                                    Conferences, Workshops & Lectures
                                </p>
                            </div>
                        </div>
                        {lastUpdated && (
                            <div className="text-xs text-gray-400">
                                Updated: {new Date(lastUpdated).toLocaleDateString()}
                            </div>
                        )}
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Filter Bar */}
                <FilterBar
                    filters={filters}
                    setFilters={setFilters}
                    sortBy={sortBy}
                    setSortBy={setSortBy}
                    organizations={organizations}
                    eventCount={filteredEvents.length}
                    totalCount={events.length}
                />

                {/* Content */}
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-200 border-t-primary-600"></div>
                    </div>
                ) : error ? (
                    <div className="glass-card rounded-xl p-8 text-center">
                        <div className="text-red-500 text-lg font-medium mb-2">Unable to load events</div>
                        <p className="text-gray-500">{error}</p>
                    </div>
                ) : (
                    <EventList events={filteredEvents} />
                )}
            </main>

            {/* Footer */}
            <footer className="border-t border-purple-100 mt-12 py-6">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
                    <p>
                        Aggregating psychoanalytic events from leading organizations worldwide.
                        Data updates daily.
                    </p>
                </div>
            </footer>
        </div>
    )
}

export default App
