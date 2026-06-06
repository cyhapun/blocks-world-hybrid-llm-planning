(define (problem bw_easy_007)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on c a)
    (clear c)
    (clear b)
    (handempty)
  )

  (:goal
    (on a b)
  )
)
