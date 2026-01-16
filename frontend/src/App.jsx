import { useState, useEffect, useMemo } from 'react'
import { useEvents } from './hooks/useEvents'
import FilterBar from './components/FilterBar'
import EventList from './components/EventList'
import SubmitEventModal from './components/SubmitEventModal'

// Data URL - update this after deployment
const DATA_URL = './data/events.json'
const SOURCES_URL = './data/sources.json'

function App() {
    const { events, loading, error, lastUpdated } = useEvents(DATA_URL)
    const [sourcesCount, setSourcesCount] = useState(0)
    const [showSubmitModal, setShowSubmitModal] = useState(false)
    const [filters, setFilters] = useState({
        search: '',
        format: [],
        eventType: [],
        startDate: '',
        endDate: '',
        organization: '',
    })
    const [sortBy, setSortBy] = useState('date')

    // Load sources count
    useEffect(() => {
        fetch(SOURCES_URL)
            .then(res => res.json())
            .then(sources => {
                const enabledCount = sources.filter(s => s.enabled).length
                setSourcesCount(enabledCount)
            })
            .catch(() => setSourcesCount(0))
    }, [])

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
            <header className="glass-card sticky top-0 z-50 border-b border-slate-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)' }}>
                                <span className="text-white text-xl font-serif">ψ</span>
                            </div>
                            <div>
                                <h1 className="text-xl font-display font-bold gradient-text">
                                    Psychoanalytic Events
                                </h1>
                                <p className="text-xs text-slate-500">
                                    Conferences, Workshops & Lectures
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            {sourcesCount > 0 && (
                                <div className="stats-badge hidden sm:flex">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                                    </svg>
                                    {sourcesCount} Sources
                                </div>
                            )}
                            <button
                                onClick={() => setShowSubmitModal(true)}
                                className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                </svg>
                                <span className="hidden sm:inline">Submit Event</span>
                            </button>
                            {lastUpdated && (
                                <div className="text-xs text-slate-400 hidden md:block">
                                    Updated {new Date(lastUpdated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                </div>
                            )}
                        </div>
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
                        <div className="animate-spin rounded-full h-12 w-12 border-4 border-sky-100 border-t-sky-600"></div>
                    </div>
                ) : error ? (
                    <div className="glass-card rounded-xl p-8 text-center">
                        <div className="text-red-500 text-lg font-medium mb-2">Unable to load events</div>
                        <p className="text-slate-500">{error}</p>
                    </div>
                ) : (
                    <EventList events={filteredEvents} />
                )}
            </main>

            {/* Footer */}
            <footer className="border-t border-slate-200 mt-12 py-8 bg-slate-50/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
                        <p>
                            Aggregating psychoanalytic events from leading organizations worldwide. Data updates daily.
                        </p>
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setShowSubmitModal(true)}
                                className="hover:text-slate-700 transition-colors"
                            >
                                Submit Event
                            </button>
                            <span className="text-slate-300">|</span>
                            <span>{sourcesCount} Sources</span>
                        </div>
                    </div>
                </div>
            </footer>

            {/* Submit Modal */}
            <SubmitEventModal
                isOpen={showSubmitModal}
                onClose={() => setShowSubmitModal(false)}
            />
        </div>
    )
}

export default App
