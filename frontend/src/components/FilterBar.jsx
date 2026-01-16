import { useState } from 'react'

const FORMAT_OPTIONS = [
    { value: 'online', label: 'Online', color: 'green' },
    { value: 'in-person', label: 'In-Person', color: 'blue' },
    { value: 'hybrid', label: 'Hybrid', color: 'purple' },
]

const EVENT_TYPES = [
    { value: 'conference', label: 'Conference' },
    { value: 'workshop', label: 'Workshop' },
    { value: 'lecture', label: 'Lecture' },
    { value: 'seminar', label: 'Seminar' },
    { value: 'webinar', label: 'Webinar' },
    { value: 'course', label: 'Course' },
]

export default function FilterBar({
    filters,
    setFilters,
    sortBy,
    setSortBy,
    organizations,
    eventCount,
    totalCount
}) {
    const [isExpanded, setIsExpanded] = useState(false)

    const handleSearchChange = (e) => {
        setFilters(prev => ({ ...prev, search: e.target.value }))
    }

    const toggleFormat = (format) => {
        setFilters(prev => ({
            ...prev,
            format: prev.format.includes(format)
                ? prev.format.filter(f => f !== format)
                : [...prev.format, format]
        }))
    }

    const toggleEventType = (type) => {
        setFilters(prev => ({
            ...prev,
            eventType: prev.eventType.includes(type)
                ? prev.eventType.filter(t => t !== type)
                : [...prev.eventType, type]
        }))
    }

    const clearFilters = () => {
        setFilters({
            search: '',
            format: [],
            eventType: [],
            startDate: '',
            endDate: '',
            organization: '',
        })
    }

    const hasActiveFilters = filters.search ||
        filters.format.length > 0 ||
        filters.eventType.length > 0 ||
        filters.startDate ||
        filters.endDate ||
        filters.organization

    return (
        <div className="glass-card rounded-2xl p-4 mb-6 animate-fade-in">
            {/* Main search bar */}
            <div className="flex flex-wrap gap-4 items-center">
                <div className="relative flex-1 min-w-[200px]">
                    <svg
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <input
                        type="text"
                        placeholder="Search events, organizations..."
                        value={filters.search}
                        onChange={handleSearchChange}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white/50 focus:bg-white transition-colors"
                    />
                </div>

                {/* Results count */}
                <div className="text-sm text-gray-500">
                    <span className="font-semibold text-primary-600">{eventCount}</span>
                    {eventCount !== totalCount && (
                        <span> of {totalCount}</span>
                    )} events
                </div>

                {/* Toggle filters button */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${isExpanded || hasActiveFilters
                        ? 'bg-primary-100 border-primary-300 text-primary-700'
                        : 'border-slate-200 text-gray-600 hover:border-primary-300'
                        }`}
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                    </svg>
                    Filters
                    {hasActiveFilters && (
                        <span className="w-2 h-2 rounded-full bg-accent-500 animate-pulse"></span>
                    )}
                </button>

                {/* Sort dropdown */}
                <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white/50"
                >
                    <option value="date">Sort by Date</option>
                    <option value="title">Sort by Title</option>
                    <option value="completeness">Sort by Completeness</option>
                </select>
            </div>

            {/* Expanded filters */}
            {isExpanded && (
                <div className="mt-4 pt-4 border-t border-slate-100 space-y-4">
                    {/* Format filters */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
                        <div className="flex flex-wrap gap-2">
                            {FORMAT_OPTIONS.map(option => (
                                <button
                                    key={option.value}
                                    onClick={() => toggleFormat(option.value)}
                                    className={`badge cursor-pointer transition-all ${filters.format.includes(option.value)
                                        ? `badge-${option.value} ring-2 ring-offset-1 ring-${option.color}-400`
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Event type filters */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Event Type</label>
                        <div className="flex flex-wrap gap-2">
                            {EVENT_TYPES.map(option => (
                                <button
                                    key={option.value}
                                    onClick={() => toggleEventType(option.value)}
                                    className={`badge cursor-pointer transition-all ${filters.eventType.includes(option.value)
                                        ? 'bg-primary-100 text-primary-700 ring-2 ring-offset-1 ring-primary-400'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Date range and organization */}
                    <div className="flex flex-wrap gap-4">
                        <div className="flex-1 min-w-[150px]">
                            <label className="block text-sm font-medium text-gray-700 mb-2">From Date</label>
                            <input
                                type="date"
                                value={filters.startDate}
                                onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
                                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/50"
                            />
                        </div>
                        <div className="flex-1 min-w-[150px]">
                            <label className="block text-sm font-medium text-gray-700 mb-2">To Date</label>
                            <input
                                type="date"
                                value={filters.endDate}
                                onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
                                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/50"
                            />
                        </div>
                        <div className="flex-1 min-w-[200px]">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Organization</label>
                            <select
                                value={filters.organization}
                                onChange={(e) => setFilters(prev => ({ ...prev, organization: e.target.value }))}
                                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/50"
                            >
                                <option value="">All Organizations</option>
                                {organizations.map(org => (
                                    <option key={org} value={org}>{org}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Clear filters button */}
                    {hasActiveFilters && (
                        <button
                            onClick={clearFilters}
                            className="text-sm text-primary-600 hover:text-primary-800 font-medium"
                        >
                            Clear all filters
                        </button>
                    )}
                </div>
            )}
        </div>
    )
}
