const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

class CalendarService {
  /**
   * Get calendar authorization URL
   * Uses cookies for authentication (credentials: 'include')
   */
  async getCalendarAuthUrl() {
    const response = await fetch(`${API_BASE_URL}/calendar/auth-url`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Use cookies instead of Bearer token
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to get calendar authorization URL');
    }

    const data = await response.json();
    return data.data.authUrl;
  }

  /**
   * Check if calendar is connected
   */
  async getConnectionStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/calendar/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Use cookies
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      return data.data.isConnected;
    } catch (error) {
      console.error('Error checking calendar connection:', error);
      return false;
    }
  }

  /**
   * Get calendar events
   */
  async getEvents(startDate, endDate) {
    const params = new URLSearchParams({
      start: startDate.toISOString(),
      end: endDate.toISOString(),
    });

    const response = await fetch(`${API_BASE_URL}/calendar/events?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Use cookies
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to fetch calendar events');
    }

    const data = await response.json();
    return data.data.events;
  }

  /**
   * Create calendar event directly
   */
  async createEvent(eventData) {
    const response = await fetch(`${API_BASE_URL}/calendar/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Use cookies
      body: JSON.stringify(eventData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to create calendar event');
    }

    const data = await response.json();
    return data.data.event;
  }

  /**
   * Create calendar event from email
   */
  async createEventFromEmail(emailId) {
    const response = await fetch(`${API_BASE_URL}/calendar/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Use cookies
      body: JSON.stringify({ emailId }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to create calendar event from email');
    }

    const data = await response.json();
    return data.data;
  }

  /**
   * Update calendar event
   */
  async updateEvent(eventId, eventData) {
    const response = await fetch(`${API_BASE_URL}/calendar/events/${eventId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Use cookies
      body: JSON.stringify(eventData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to update calendar event');
    }

    const data = await response.json();
    return data.data.event;
  }

  /**
   * Get all stored calendar events (no date filter)
   */
  async getAllEvents() {
    const response = await fetch(`${API_BASE_URL}/calendar/events/all`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to fetch all calendar events');
    }
    const data = await response.json();
    return data.data.events;
  }

  /**
   * Delete calendar event — pass the googleEventId field from the DB doc
   */
  async deleteEvent(googleEventId) {
    const response = await fetch(`${API_BASE_URL}/calendar/events/${googleEventId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Use cookies
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to delete calendar event');
    }

    return true;
  }

  /**
   * Disconnect calendar
   */
  async disconnectCalendar() {
    const response = await fetch(`${API_BASE_URL}/calendar/disconnect`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Use cookies
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to disconnect calendar');
    }

    return true;
  }
}

export const calendarService = new CalendarService();