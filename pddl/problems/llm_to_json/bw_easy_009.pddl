(define (problem bw_easy_009)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table b)
    (on_table c)
    (on a c)
    (clear a)
    (clear b)
    (handempty)
  )

  (:goal
    (on b a)
  )
)
