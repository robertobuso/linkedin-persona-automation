import { z } from 'zod'

export const emailSchema = z.string().email('Invalid email address')

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')

export const postContentSchema = z
  .string()
  .min(10, 'Post content must be at least 10 characters')
  .max(3000, 'Post content must not exceed 3000 characters')

export const hashtagSchema = z
  .string()
  .regex(/^#[a-zA-Z0-9_]+$/, 'Invalid hashtag format')

export function validateHashtags(hashtags: string[]) {
  const errors: string[] = []
  
  if (hashtags.length === 0) {
    errors.push('At least one hashtag is required')
  }
  
  if (hashtags.length > 10) {
    errors.push('Maximum 10 hashtags allowed')
  }
  
  hashtags.forEach((tag, index) => {
    try {
      hashtagSchema.parse(tag)
    } catch (error) {
      errors.push(`Hashtag ${index + 1}: ${tag} is invalid`)
    }
  })
  
  return errors
}

export function validateUrl(url: string) {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export function sanitizeContent(content: string) {
  // Remove potentially harmful content
  return content
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .trim()
}
