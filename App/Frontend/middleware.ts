import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  console.log('Middleware running for:', request.url)
  const authStorage = request.cookies.get('auth-storage')?.value
  console.log('Auth storage:', authStorage ? 'exists' : 'missing')

  if (!authStorage) {
    console.log('No auth storage, redirecting to login')
    return NextResponse.redirect(new URL('/auth/login', request.url))
  }

  try {
    const auth = JSON.parse(authStorage)
    console.log('Parsed auth:', auth)
    if (!auth.state?.accessToken) {
      console.log('No access token, redirecting to login')
      return NextResponse.redirect(new URL('/auth/login', request.url))
    }
    console.log('Auth valid, proceeding')
  } catch (error) {
    console.log('Auth parse error:', error)
    return NextResponse.redirect(new URL('/auth/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/wardrobe/:path*', '/outfits/:path*', '/profile/:path*'],
}
