import { useState, useEffect } from 'react'

export function useEvents(dataUrl) {
    const [events, setEvents] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [lastUpdated, setLastUpdated] = useState(null)

    useEffect(() => {
        async function fetchEvents() {
            try {
                setLoading(true)
                setError(null)

                const response = await fetch(dataUrl)
                if (!response.ok) {
                    throw new Error(`Failed to fetch events: ${response.status}`)
                }

                const data = await response.json()

                // Handle both formats: direct array or wrapped object
                if (Array.isArray(data)) {
                    setEvents(data)
                } else if (data.events) {
                    setEvents(data.events)
                    if (data.metadata?.last_updated) {
                        setLastUpdated(data.metadata.last_updated)
                    }
                } else {
                    setEvents([])
                }
            } catch (err) {
                console.error('Failed to load events:', err)
                setError(err.message)
                setEvents([])
            } finally {
                setLoading(false)
            }
        }

        fetchEvents()
    }, [dataUrl])

    return { events, loading, error, lastUpdated }
}
